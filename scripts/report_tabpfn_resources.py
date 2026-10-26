"""Xuất báo cáo tài nguyên từ các phép đo thật, giữ riêng ngoại suy."""

import argparse
import json
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument('version', choices=['V3', 'V3_5'])
    version = p.parse_args().version
    root = Path(__file__).resolve().parents[1]
    folder = root / 'reports/tabpfn_resources_20261024' / version
    decision = json.loads((folder / 'decision.json').read_text(encoding='utf-8'))
    lines = [f'# Đánh giá tài nguyên TabPFN {version}', '',
             'Chỉ dùng frozen embeddings train, 384 chiều float32; seed42, lấy mẫu phân tầng. Không dùng validation/test để chọn cấu hình tài nguyên. `tabpfn==9.2.0`, phiên bản explicit, n_estimators1, memory_saving_mode=True, keep_cache_on_device=False. Không PCA/SVD hoặc text preprocessing.', '',
             '| Phép đo | Mẫu | Chế độ | Lô | Fit s | Predict s | RSS byte | GPU allocated byte | GPU reserved byte | Trạng thái |',
             '|---|---:|---|---:|---:|---:|---:|---:|---:|---|']
    errors = []
    for path in sorted(folder.glob('*.json')):
        if path.name == 'decision.json':
            continue
        row = json.loads(path.read_text(encoding='utf-8'))
        lines.append('| ' + ' | '.join(str(v) for v in [path.stem, row['samples'],
            row.get('settings', {}).get('fit_mode', 'NOT_MEASURED'), row.get('prediction_batch_size'),
            row.get('fit_seconds', 'NOT_MEASURED'), row.get('inference_seconds', 'NOT_MEASURED'),
            row.get('peak_process_rss_bytes', 'NOT_MEASURED'), row.get('peak_gpu_allocated_bytes', 'NOT_MEASURED'),
            row.get('peak_gpu_reserved_bytes', 'NOT_MEASURED'), row['status']]) + ' |')
        if 'error' in row:
            errors.append(f'- `{path.name}`: ' + row['error'].replace('\n', ' '))
    if errors:
        lines += ['', '## Lỗi đã quan sát', '', *errors]
    lines += ['', '## Quyết định trước experiment', '',
              '```json', json.dumps(decision, ensure_ascii=False, indent=2), '```', '',
              'RSS là bộ nhớ toàn tiến trình lấy mẫu20ms, không phải giới hạn cứng của hệ điều hành. GPU allocated/reserved do PyTorch báo cáo có thể bao gồm bộ nhớ chia sẻ Windows; không diễn giải reserved là VRAM vật lý. Phép đo nằm trong tiến trình riêng, không phải RSS toàn máy.', '',
              'V3: đủ21K đã thử với official memory-saving và nhiều lô; cached vượt trần RSS6GB, low_memory lô nhỏ có chi phí ngoại suy validation/reload/test vượt1800s. V3.5: dừng tăng mẫu sau phép đo5000 vì RSS9,14GB; full21K chưa đo, không tuyên bố OOM. Cả hai có thử CPU precision auto: guard thư viện chặn >5000 mẫu; không bỏ guard trên máy16GB. Quyết định riêng từng model được ghi ở JSON phía trên; dùng subsample train seed42, giữ tỷ lệ lớp, không giảm chiều embedding.', '',
              'Đây là phép đo kỹ thuật; không phải kết quả chất lượng mô hình. Chỉ laptop, rating-derived proxy labels có nhiễu; không có human gold trong phép đo.', '',
              'Follow-up full21000 trên cloud mới là PENDING: xem `docs/TABPFN_CLOUD_PLAN.md`. GPU24GB/RAM32GB hoặc A10040GB/RAM64GB chỉ là đề xuất đo mới, không phải cloud đã PASS. Không thay decision hoặc số liệu local trong báo cáo này.']
    name = 'p5_e03_tabpfn_v3' if version == 'V3' else 'p5_e04_tabpfn_v35'
    (root / 'reports' / (name + '_resource_assessment.md')).write_text('\n'.join(lines)+'\n', encoding='utf-8')


if __name__ == '__main__':
    main()
