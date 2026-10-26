"""Bổ sung Model Readiness Analysis từ dataset bất biến; không chạy lại EDA."""

import json

import numpy as np
import pandas as pd
from tokenizers import Tokenizer

from scripts.revalidate_model_data import write_json
from src.config import PROJECT_ROOT
from src.data.acquisition import sha256_file
from src.preprocessing.semantic import canonical_text


def main() -> None:
    root = PROJECT_ROOT
    prior = json.loads((root / 'reports/p2_revalidation_for_new_models.json').read_text(encoding='utf-8'))
    path = root / 'data/processed/laptop_reviews.parquet'
    if prior['status'] != 'PASS' or sha256_file(path) != prior['dataset_sha256']:
        raise ValueError('P2 chưa PASS hoặc dataset thay đổi')
    frame = pd.read_parquet(path)
    texts = canonical_text(frame)
    tokenizer = Tokenizer.from_file(str(root / 'artifacts/preprocessing/p4_20261009_final/bert/tokenizer.json'))
    tokenizer.no_truncation()
    tokenizer.no_padding()
    lengths = []
    for start in range(0, len(texts), 128):
        lengths.extend(len(e.ids) for e in tokenizer.encode_batch(texts[start:start+128]))
    series = {'characters': np.array([len(t) for t in texts]),
              'words': np.array([len(t.split()) for t in texts]),
              'bert_wordpiece_including_special_tokens': np.array(lengths)}
    percentiles = {name: {**{f'p{q}': float(np.percentile(values, q)) for q in [50, 75, 90, 95, 99]},
                           'max': int(values.max()), 'min': int(values.min())}
                   for name, values in series.items()}
    counts = frame.sentiment.value_counts()
    result = {'status': 'PASS', 'rows': len(frame), 'products': int(frame.parent_asin.nunique()),
              'class_counts': {k: int(v) for k, v in counts.items()},
              'class_shares': {k: float(v / len(frame)) for k, v in counts.items()},
              'product_review_count_percentiles': {str(k): float(v) for k, v in frame.parent_asin.value_counts().quantile([.5, .75, .9, .95, .99, 1]).items()},
              'missing_or_blank': {c: int((frame[c].isna() | frame[c].fillna('').str.strip().eq('')).sum()) for c in ['review_title', 'text']},
              'length_percentiles': percentiles,
              'above_token_limit_share': {str(n): float((series['bert_wordpiece_including_special_tokens'] > n).mean()) for n in [128, 256, 512]},
              'token_measurement': 'BERT WordPiece thực trên canonical text; chỉ xấp xỉ đối với encoder khác',
              'storage_estimate_bytes': {str(dim): {dtype: len(frame) * dim * size for dtype, size in [('float32', 4), ('float16', 2)]} for dim in [384, 768]},
              'train_rows': 21000, 'neutral_train_rows': 1842,
              'dataset_sha256': sha256_file(path),
              'resource_measurements': 'NOT_MEASURED: benchmark encoder P4 và smoke từng model P5/P6 còn chờ'}
    write_json(root / 'reports/p3_model_readiness.json', result)
    lines = ['# P3 — Model Readiness Analysis', '', 'Trạng thái: PASS cho phân tích readiness; khả thi tài nguyên từng model còn WARNING.', '',
             'Không chạy lại EDA cũ; giữ nguyên 15 bảng/7 hình và các nhận định lịch sử.', '',
             f'Có {len(frame):,} review / {frame.parent_asin.nunique():,} sản phẩm; nhãn: {result["class_counts"]}.', '',
             'Neutral chỉ 8,77%; train có 1.842 neutral. Accuracy dễ che lỗi lớp này: chọn bằng macro F1, báo neutral F1 và đối chiếu weighted/unweighted trên validation. Không SMOTE.', '',
             f'Title/body thiếu hoặc trống: {result["missing_or_blank"]}.', '',
             '| Độ dài canonical text | p50 | p75 | p90 | p95 | p99 | max |', '|---|---:|---:|---:|---:|---:|---:|']
    for name, values in percentiles.items():
        lines.append('| ' + name + ' | ' + ' | '.join(str(round(values[k], 2)) for k in ['p50', 'p75', 'p90', 'p95', 'p99', 'max']) + ' |')
    lines += ['', f'Tỷ lệ vượt 128/256/512 WordPiece: {result["above_token_limit_share"]}. Đây là số đếm bằng tokenizer BERT có special tokens; không giả là token count chính xác của mọi encoder.', '',
              f'Ước lượng dung lượng embeddings (byte, chưa gồm metadata): {result["storage_estimate_bytes"]}.', '',
              '| Model | Kết luận về dữ liệu | Ước lượng/rủi ro tài nguyên |', '|---|---|---|',
              '| XGBoost | 21K × dense features đủ để thử; không bảo đảm điểm số | Input 384 chiều float32 khoảng 32,26 MB; cây/histogram cần thêm RAM; CPU hist là lựa chọn an toàn ban đầu |',
              '| TabM | 21K với ba lớp đủ để thử | Tham số/activation phụ thuộc width, k, batch; đo VRAM smoke trước full; weighted loss cần validation |',
              '| TabPFN-3 | Dữ liệu số 384 chiều phù hợp API; chưa chứng minh full 21K khả thi | Context attention/cache có thể vượt 6 GB; dùng low_memory/memory_saving chính thức trước khi cân nhắc subsample riêng |',
              '| TabPFN-3.5 | Dữ liệu như V3; checkpoint phải riêng | Không suy từ V3 rằng V3.5 vừa VRAM; đo riêng và giữ 21K cho các model khác |',
              '| Transformer | 21K có thể fine-tune; neutral cần kiểm tra riêng | BERT ~110M tham số: riêng FP32 weights khoảng 440 MB, optimizer/gradient/activation lớn hơn; batch nhỏ + FP16 + accumulation + checkpointing; smoke trước full |', '',
              'Các chi phí trong bảng là ước lượng cấu trúc, không phải peak RAM/VRAM đo được. Benchmark P4/P5/P6 sẽ quyết định tính khả thi thực tế; không hạ kích thước dataset để làm đẹp kết quả.', '',
              'Full-data readiness chỉ mô tả, không dùng nhãn test chọn feature, max_length, hyperparameter hoặc model. Chính sách tokenizer mới sẽ cố định trước training; max_length 512 giữ từ P4 train-derived cũ.', '',
              'Bằng chứng chi tiết: `p3_model_readiness.json`. Giới hạn: chỉ laptop; proxy labels nhiễu; shift SemEval–Amazon trong laptop; gold thủ công nhỏ, hiện chưa có.']
    (root / 'reports/p3_model_readiness.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'PASS', 'length_percentiles': percentiles}, ensure_ascii=True))


if __name__ == '__main__':
    main()
