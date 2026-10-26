"""Tổng hợp báo cáo từ kết quả đã lưu, không chạy dự đoán hoặc chọn lại bằng test."""

import json
import pandas as pd

from scripts.train_modern import ORDER, latest_report
from src.config import PROJECT_ROOT
from src.preprocessing.semantic_cache import load_semantic_config


def collect(include_transformer=False):
    root = PROJECT_ROOT
    cfg = load_semantic_config()
    results, rows = {}, []
    for name in ORDER + (['E05_transformer'] if include_transformer else []):
        folder = latest_report(root / cfg['reports'] / name)
        r = json.loads((folder / 'result.json').read_text(encoding='utf-8'))
        assert r['status'] == 'PASS' and (folder / 'independent_validation.json').exists()
        results[name] = r
        m = r['test_metrics']
        rows.append({'model': name, 'train_samples': r['train_rows'],
            'data_regime': r.get('data_regime', 'FULL'),
            'representation': 'N/A' if name == ORDER[0] else 'canonical raw text → BERT' if name == 'E05_transformer' else 'frozen MiniLM384',
            'validation_macro_f1': r['validation_macro_f1'],
            **{key: m[key] for key in ['macro_f1', 'accuracy', 'weighted_f1', 'balanced_accuracy']},
            **{f'{label}_f1': m['per_class'][label]['f1'] for label in ['negative', 'neutral', 'positive']},
            'runtime_seconds': r['runtime_seconds'], 'peak_gpu_allocated_bytes': r['peak_gpu_allocated_bytes'],
            'peak_process_rss_bytes': r['peak_process_rss_bytes'], 'artifact_bytes': r['artifact_bytes'],
            'artifact_file_bytes_actual': sum(p.stat().st_size for p in (root / r.get('artifact_directory', f'{cfg["experiments"]}/{name}')).rglob('*') if p.is_file()),
            'inference_ms_per_review': r['inference_ms_per_review']})
    return results, pd.DataFrame(rows)


def markdown_table(frame):
    columns = ['model', 'train_samples', 'data_regime', 'representation', 'macro_f1', 'accuracy',
               'weighted_f1', 'balanced_accuracy', 'negative_f1', 'neutral_f1', 'positive_f1',
               'runtime_seconds', 'peak_gpu_allocated_bytes']
    lines = ['| ' + ' | '.join(columns) + ' |', '|' + '|'.join(['---']*len(columns)) + '|']
    for _, row in frame.iterrows():
        lines.append('| ' + ' | '.join(f'{row[c]:.6f}' if isinstance(row[c], float) else str(row[c]) for c in columns) + ' |')
    return '\n'.join(lines)


LIMITATIONS = ('Chỉ review laptop tiếng Anh. Các chỉ số đo dự đoán nhãn đại diện suy từ Amazon star rating '
    '(rating-derived sentiment proxy), có nhiễu; không phải độ chính xác so với human sentiment gold. '
    'Neutral8,77%; một seed42/search nhỏ; test đã dùng ở LEGACY nên không hoàn toàn unseen của toàn dự án. '
    'SemEval-to-Amazon platform/style shift trong laptop là giới hạn của phần ABSA tương lai, ngoài benchmark chỉ-Amazon này; bộ gold thủ công dự kiến nhỏ, hiện chưa có. '
    'Human-gold evaluation remains future work. Không triển khai ABSA hoặc mô hình tiếng Việt trong tác vụ này.')

FOLLOWUP = ('Follow-up TabPFN full21000 trên cloud: PENDING, chưa upload/thuê GPU/chạy job. '
            'Xem `docs/TABPFN_CLOUD_PLAN.md`; giữ kết quả local, output cloud riêng và công bố test reuse. '
            'Không rerun baseline/BERT chỉ để chuyển TabPFN lên cloud.')


_cloud_receipt = PROJECT_ROOT / 'reports/p7_completion.json'
if _cloud_receipt.exists() and json.loads(_cloud_receipt.read_text(encoding='utf-8')).get('model_sources'):
    FOLLOWUP = ('Cloud full21000 đã verified; xem reports/tabpfn_kaggle_full21k_verification.md và P7 hiện hành. '
                'Các kết quả local trong báo cáo P5 này giữ ngữ cảnh lịch sử/subsample; không ghi đè artifacts hoặc rerun model.')


def p5_report():
    root = PROJECT_ROOT
    results, frame = collect()
    frame.to_csv(root / 'reports/p5_modern_results.csv', index=False)
    from src.sentiment.tabpfn_versions import version_resolution
    from tabpfn.model_loading import resolve_model_version
    from pathlib import Path
    paths = version_resolution()
    version_report = {'status': 'PASS', 'E03': {'requested_version': 'V3', 'resolved_version': resolve_model_version(Path(paths[ORDER[3]])).name,
        'checkpoint': paths[ORDER[3]]}, 'E04': {'requested_version': 'V3_5', 'resolved_version': resolve_model_version(Path(paths[ORDER[4]])).name,
        'checkpoint': paths[ORDER[4]]}}
    assert version_report['E03']['checkpoint'] != version_report['E04']['checkpoint']
    (root / 'reports/tabpfn_version_verification.json').write_text(json.dumps(version_report, indent=2), encoding='utf-8')
    text = '\n'.join(['# P5 — So sánh các mô hình bảng', '',
        'Trạng thái: PASS về thực thi/metrics; LIMITED về dữ liệu TabPFN, WARNING về RSS E03. Không phải tất cả mô hình dùng full train. Các baseline E00/E01/E02 được reuse, không retrain hoặc predict test lại.', '',
        markdown_table(frame), '', FOLLOWUP, '',
        'Selection dựa trên validation macro F1; cấu hình/checkpoint được khóa trước test. Artifact, prediction review_id, per-class precision/recall/F1 và confusion matrix nằm trong `reports/semantic_20261024/`, E03 dưới `attempts/resource01`. Các independent_validation.json đã tính lại metrics và kiểm tra thứ tự ID. Token không được lưu.', '',
        'TabPFN-3 dùng10000 mẫu, TabPFN-3.5 dùng1500 mẫu phân tầng seed42; cùng embedding384, không PCA/SVD. Quyết định theo đo train-only, không dựa trên test. Xem hai `p5_e0*_resource_assessment.md` và JSON thô. V3 nhận384 chiều nhưng default n_estimators1 chỉ phủ tối đa200 chiều bên trong model theo cảnh báo thư viện; không được diễn giải là so sánh classifier hoàn toàn kiểm soát. Không sửa sau khi xem test.', '',
        'WARNING: E03 RSS thực6482808832byte vượt trần cấu hình6GB; phép đo riêng10K là5816950784byte nên không dự báo đầy đủ overhead runner/serialization/reload. Bộ monitor lúc E03 chỉ ghi nhận, chưa enforce RSS; đã thêm chặn trước test cho E04. Không chạy lại test E03 để che giới hạn. E03 không OOM; không khẳng định full21K không thể chạy ở mọi cấu hình/máy. Guard mới có thể từ chối retry10K nếu RSS vượt6GB ở máy/lần chạy khác; cần đo lại train-only và suffix mới, không mở lại test đã khóa.', '',
        'Hai version/checkpoint phân biệt thực qua API đã kiểm tra tại `tabpfn_version_verification.json`. Chi phí TabPFN là pretrained foundation model + fit/in-context inference, không phải huấn luyện từ đầu như TabM/XGBoost.', '', LIMITATIONS, ''])
    (root / 'reports/p5_modern_tabular_models.md').write_text(text, encoding='utf-8')
    for name, filename in [(ORDER[3], 'p5_e03_tabpfn_v3.md'), (ORDER[4], 'p5_e04_tabpfn_v35.md')]:
        row = frame[frame.model == name]
        (root / 'reports' / filename).write_text('\n'.join([f'# {name}', '', markdown_table(row), '',
            'Trạng thái LIMITED/SUBSAMPLED; experiment kỹ thuật PASS. Chi tiết config/version/seed/provenance, predictions, full metrics, confusion matrix, selection lock và resource usage trong thư mục report experiment. Xem báo cáo P5 chung và resource assessment về giới hạn, đặc biệt RSS E03 và feature coverage V3. Không test tuning.', '', FOLLOWUP, '', LIMITATIONS, '']), encoding='utf-8')


if __name__ == '__main__':
    p5_report()
