"""P7: tổng hợp đánh giá đã khóa, phân tích lỗi mô tả, không quay lại tuning."""

import json
import re

import numpy as np
import pandas as pd

from scripts.benchmark_reports import collect, markdown_table, LIMITATIONS, FOLLOWUP
from scripts.revalidate_model_data import write_json
from scripts.train_modern import latest_report
from src.config import PROJECT_ROOT
from src.preprocessing.semantic import canonical_text
from src.preprocessing.semantic_cache import load_semantic_config


def redact_excerpt(text):
    """Ẩn các mẫu thông tin cá nhân phổ biến; không phải audit PII bằng người."""
    text = re.sub(r'https?://\S+|\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b', '[ẩn liên hệ]', text)
    text = re.sub(r'(?<!\w)\+?\d[\d ()-]{7,}\d(?!\w)', '[ẩn số]', text)
    text = re.sub(r'(?i)\bmy name is\s+\w+(?:\s+\w+)?', '[ẩn tên]', text)
    return text[:220]


def error_analysis(results):
    root = PROJECT_ROOT
    cfg = load_semantic_config()
    frame = pd.read_parquet(root / cfg['splits'] / 'test.parquet')
    texts = canonical_text(frame)
    sizes = np.array([len(t.split()) for t in texts])
    masks = {'short_10_words': sizes <= 10, 'long_200_words': sizes > 200,
        'negation_cue': np.array([bool(re.search(r"\b(no|not|never|without)\b|n't", t, re.I)) for t in texts]),
        'mixed_cues_heuristic': np.array([bool(re.search(r'\b(good|great|excellent|love)\b', t, re.I)) and
            bool(re.search(r'\b(bad|poor|broken|slow|hate)\b', t, re.I)) for t in texts]),
        'ambiguous_requires_human_review': frame.label_id.to_numpy() == 1}
    groups, examples, transitions = [], [], []
    for name in results:
        report = latest_report(root / cfg['reports'] / name)
        prediction = pd.read_parquet(report / 'test_predictions.parquet')
        assert frame.review_id.tolist() == prediction.review_id.tolist()
        truth, pred = frame.label_id.to_numpy(), prediction.prediction_id.to_numpy()
        errors = truth != pred
        for a, b in [(1, 2), (1, 0), (0, 2), (2, 0)]:
            transitions.append({'model': name, 'proxy_label_id': a, 'prediction_id': b,
                                'count': int(((truth == a) & (pred == b)).sum())})
        for category, mask in masks.items():
            groups.append({'model': name, 'category': category, 'support': int(mask.sum()),
                           'errors': int((mask & errors).sum()),
                           'proxy_disagreement_rate': float(errors[mask].mean()) if mask.any() else None})
            for i in np.flatnonzero(mask & errors)[:3]:
                examples.append({'review_id': frame.review_id.iloc[i], 'model': name,
                    'text_excerpt': redact_excerpt(texts[i]), 'proxy_label': ['negative','neutral','positive'][truth[i]],
                    'prediction': ['negative','neutral','positive'][pred[i]], 'confidence': None,
                    'error_category': category, 'human_verified': False,
                    'star_text_mismatch': 'PENDING: cần người phân biệt lỗi model với nhiễu nhãn sao'})
    pd.DataFrame(groups).to_csv(root / 'reports/p7_error_groups.csv', index=False)
    pd.DataFrame(examples).to_csv(root / 'reports/p7_error_examples.csv', index=False)
    pd.DataFrame(transitions).to_csv(root / 'reports/p7_error_transitions.csv', index=False)
    return groups, transitions


def finish():
    root = PROJECT_ROOT
    completion_file = root / 'reports/p7_completion.json'
    if completion_file.exists() and json.loads(completion_file.read_text(encoding='utf-8')).get('model_sources'):
        from scripts.publish_kaggle_results import publish
        publish(root)
        return
    cfg = load_semantic_config()
    results, frame = collect(include_transformer=True)
    frame.to_csv(root / 'reports/p7_unified_results.csv', index=False)
    groups, transitions = error_analysis(results)
    competitive = frame[frame.model != 'E00_majority']
    best = competitive.loc[competitive.validation_macro_f1.idxmax()]
    frozen = frame[frame.model.str.contains('embedding')]
    best_frozen = frozen.loc[frozen.validation_macro_f1.idxmax()]
    p6 = results['E05_transformer']
    history = json.loads((root / cfg['reports'] / 'E05_transformer/history.json').read_text(encoding='utf-8'))
    p6text = ['# P6 — Transformer canonical title + body', '',
        'PASS: fine-tune end-to-end BERT trên đủ21000 mẫu train; không dùng frozen embeddings làm đầu vào. Reuse infrastructure và pretrained weights, không reuse fine-tuned BERT LEGACY hoặc test score cũ.', '',
        markdown_table(frame[frame.model == 'E05_transformer']), '', FOLLOWUP, '',
        'Config đầy đủ: `configs/transformer_benchmark.yaml`; model/tokenizer revision `86b5e0934494bd15c9632b12f734a8a67f723594`, google-bert/bert-base-uncased, canonical tokens max512. AdamW2e-5/weight_decay0.01, linear warmup0.1, batch8/accum4/fp16, seed42, tối đa3epochs/patience1. Hai loss cùng khởi tạo từ pretrained weights; weights nghịch tần số chỉ từ train. Selection chỉ validation macro F1, test một lần sau selection lock và reload parity. Confidence không hiệu chuẩn, không tạo điểm tin cậy.', '',
        '| Loss | Epoch | Validation macro F1 | Neutral precision | Neutral recall | Neutral F1 | Epoch s |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for h in history:
        n = h['validation']['per_class']['neutral']
        p6text.append(f"| {h['mode']} | {h['epoch']} | {h['validation']['macro_f1']:.6f} | {n['precision']:.6f} | {n['recall']:.6f} | {n['f1']:.6f} | {h['seconds']:.3f} |")
    p6text += ['', f"Chọn loss `{p6['selected_spec']['mode']}`. Checkpoint tốt nhất, history/class weights, config, source hash, smoke forward/backward, prediction review_id, full metrics và independent validation nằm trong `{cfg['reports']}/E05_transformer/`; trọng số ở `{p6['artifact_directory']}`.", '', LIMITATIONS, '']
    (root / 'reports/p6_transformer_benchmark.md').write_text('\n'.join(p6text), encoding='utf-8')
    text = ['# P7 — Đánh giá thống nhất', '',
        'PASS: đủ6 mô hình, P5 TabPFN LIMITED/SUBSAMPLED; E03 có WARNING RSS. Đánh giá proxy-label sau khi khóa tất cả lựa chọn, không dùng phân tích lỗi để tune.', '', FOLLOWUP, '', markdown_table(frame), '',
        f"Mô hình chọn theo validation macro F1: **{best['model']}**; test macro F1={best['macro_f1']:.6f}, neutral F1={best['neutral_f1']:.6f}. Không chọn theo accuracy hoặc chọn lại bằng test.", '',
        '## Comparison A — Cùng frozen semantic representation', '',
        f"Best frozen theo validation: {best_frozen['model']}. XGBoost/TabM/TabPFN nhận cùng384 chiều frozen MiniLM. TabPFN dùng10000/1500 mẫu, còn XGBoost/TabM dùng21000: quy mô khác và V3 chỉ phủ tối đa200 chiều nội bộ với n_estimators1. Do đó bảng mô tả các cấu hình đã đo, không chứng minh thứ hạng architecture khi cùng số mẫu/hyperparameter budget. Macro/neutral F1 quan trọng hơn accuracy; TabPFN ở cấu hình này hầu như không dự đoán neutral.", '',
        '## Comparison B — Frozen representation và NLP end-to-end', '',
        'Đối chiếu best frozen với BERT fine-tune canonical text. Cả representation, context256/512 và training paradigm khác nhau; không diễn giải là so sánh architecture thuần túy. Không kiểm định nhiều seed hoặc khẳng định ý nghĩa thống kê.', '',
        '## Computational Cost', '',
        'CSV gốc `p7_unified_results.csv` có RSS, latency và artifact bytes, kèm artifact_file_bytes_actual tính lại từ tệp thực gồm metadata. Runtime là tổng experiment/search/reload/test được monitor, không đồng nhất với thời gian fit đơn lẻ. Fit-only được đo riêng trong resource assessment TabPFN; fit-only tách biệt cho campaign BERT/TabM/XGBoost NOT_MEASURED ở runner hiện tại. Epoch time BERT gồm validation. Encoder frozen dùng chung: train128 mẫu đo0.147678s sau load/warmup; không có phép đo thời gian toàn bộ30K đáng tin để phân bổ cho từng classifier (NOT_MEASURED). BERT có tokenizer riêng; thời gian tokenization toàn30K NOT_MEASURED. Không cộng tokenization vào training một cách giả định.', '',
        'XGBoost học cây trên CPU2threads; TabM học neural parameters bằng GPU, retrain cần optimizer/epochs. TabPFN sử dụng pretrained weights và ngữ cảnh train; fit_with_cache tạo cache KV trên CPU, suy luận dựa trên ngữ cảnh, không gradient-train foundation weights. Artifact joblib chứa fitted state/cache; số byte checkpoint và chi phí tạo cache khác artifact nhỏ của majority/XGBoost. BERT cập nhật toàn backbone, retrain tốn hơn và cần lại optimizer/epochs. GPU không bắt buộc về mặt API nhưng CPU large TabPFN bị guard; các experiment neural đo trên RTX4050Laptop6GB, không so runtime CPU/GPU như cùng thiết bị. GPU allocated/reserved Windows có thể gồm shared memory, không đồng nhất VRAM vật lý.', '',
        'Artifact classifier không gồm shared encoder MiniLM, tokenizer và cache embeddings; triển khai model frozen vẫn cần encoder. Latency tabular trong CSV chỉ tính predict trên embedding đã có; BERT chỉ tính forward trên token đã có. Cả hai chưa gồm tiền xử lý text/tokenization; không gọi đây là độ trễ end-to-end từ raw text. Sample encoder cost được báo riêng, không dùng để giả định chi phí toàn bộ30K.', '',
        '## Phân tích lỗi sau benchmark', '',
        '`p7_error_transitions.csv`: Neutral→Positive/Negative, Negative→Positive, Positive→Negative cho từng model. `p7_error_groups.csv`: số mẫu/lỗi theo short<=10word, long>200word, negation, mixed lexical cues, neutral ambiguous. Nhóm có thể chồng lấn; mẫu số là support từng nhóm. Không tuyên bố cue lexical là human annotation hoặc đánh giá semantic gold.', '',
        '`p7_error_examples.csv`: mẫu lỗi theo thứ tự nguồn, excerpt đã lọc mẫu liên hệ/số phổ biến, proxy label/prediction/model/category; confidence null vì chưa lưu/xác minh xác suất. human_verified=False. Mixed/ambiguous và star/text mismatch cần người đọc lại: không tự đồng nhất bất đồng với nhãn sao thành lỗi nhãn. Không có manual audit PII đầy đủ; không publish mẫu review tự động. Không tune sau phân tích lỗi.', '',
        'Đếm các chuyển nhãn của mô hình được chọn:', '', '| Proxy → Prediction | Số mẫu |', '|---|---:|']
    for row in transitions:
        if row['model'] == best['model']:
            labels = ['negative', 'neutral', 'positive']
            text.append(f"| {labels[row['proxy_label_id']]} → {labels[row['prediction_id']]} | {row['count']} |")
    text += ['', '| Nhóm mô tả | Support | Bất đồng proxy | Tỷ lệ |', '|---|---:|---:|---:|']
    for row in groups:
        if row['model'] == best['model']:
            rate = row['proxy_disagreement_rate']
            text.append(f"| {row['category']} | {row['support']} | {row['errors']} | {rate:.4f} |")
    text += ['',
        'Nhận xét từ mẫu do Codex đọc, không phải adjudication/human gold: các phàn nàn ngắn về pin hỏng, máy chậm hoặc cấu hình khác mô tả mang proxy neutral nhưng BERT dự đoán negative. Điều này cho thấy không thể đồng nhất sao3 với văn bản trung tính; chưa đủ bằng chứng khẳng định từng nhãn sao sai. Có review dài trộn khen tốc độ với phàn nàn tính năng, hoặc khen laptop trước khi nói thất vọng về tuổi thọ: dự đoán có thể bỏ sót sự chuyển cực và phạm vi phủ định. Cue phủ định cũng xuất hiện trong lời tự giới thiệu không liên quan đánh giá sản phẩm, nên chỉ đếm từ phủ định không giải thích được đúng/sai sentiment. Không thay mô hình sau khi đọc các lỗi này.', '']
    text += ['', LIMITATIONS, '']
    (root / 'reports/p7_unified_benchmark.md').write_text('\n'.join(text), encoding='utf-8')
    write_json(root / 'reports/p7_completion.json', {'status': 'PASS', 'scope': 'local_proxy_benchmark',
        'cloud_full_train_status': 'PENDING', 'models': list(results),
        'selected_by_validation': best['model'], 'best_frozen_by_validation': best_frozen['model'],
        'test_tuning': False, 'predictions_rerun': False, 'human_gold': 'FUTURE_WORK',
        'limitations': ['TabPFN SUBSAMPLED', 'E03 RSS WARNING', 'V3 internal feature coverage', 'proxy labels']})


if __name__ == '__main__':
    finish()
