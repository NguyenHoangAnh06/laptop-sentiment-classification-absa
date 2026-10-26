"""Kiểm tra P5 chỉ đọc: predictions/metrics/selection đã lưu và các tệp kết quả đáng tin cậy.

Không có khớp mô hình bất kỳ công cụ ước tính nào, chạy lại dự đoán kiểm thử hoặc sửa đổi lần chạy đã hoàn thành.
"""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import PROJECT_ROOT
from src.data.acquisition import sha256_file
from src.evaluation.classification import classification_metrics, flat_metrics
from src.sentiment.classical import load_classical, select_candidate


def validate(report: Path, root: Path = PROJECT_ROOT) -> dict:
    """Tính toán lại các số liệu một cách độc lập từ các dự đoán liên tục, không cần điều chỉnh lại kiểm thử."""
    report = Path(report)
    manifest = json.loads((report / 'manifest.json').read_text(encoding='utf-8'))
    for group in ('input_sha256', 'output_sha256', 'implementation_sha256'):
        for relative, digest in manifest[group].items():
            if sha256_file(root / relative) != digest:
                raise ValueError(f'Changed artifact: {relative}')
    lock_path = report / 'selection_lock.json'
    if sha256_file(lock_path) != manifest['selection_lock_sha256']:
        raise ValueError('Selection lock digest differs')
    lock = json.loads(lock_path.read_text(encoding='utf-8'))
    history = json.loads((report / 'training_history.json').read_text(encoding='utf-8'))
    chosen = lock['selected_candidates']
    for family, row in chosen.items():
        if row != select_candidate([r for r in history if r['family'] == family]):
            raise ValueError('Family selection inconsistent with validation scores')
    if lock['winner'] != select_candidate(list(chosen.values()))['family']:
        raise ValueError('Overall selection inconsistent with validation scores')
    config = json.loads((report / 'config.json').read_text(encoding='utf-8'))
    p4 = json.loads((root / config['p4_manifest']).read_text(encoding='utf-8'))
    models = root / 'artifacts/models' / config['output_suffix']
    predicted = pd.read_parquet(models / 'test_predictions.parquet')
    test_rows = pd.read_parquet(root / p4['paths']['preprocessing'] / 'test_feature_rows.parquet')
    pd.testing.assert_frame_equal(predicted[['review_id', 'label_id']], test_rows[['review_id', 'label_id']])
    metrics = json.loads((report / 'metrics.json').read_text(encoding='utf-8'))
    benchmark = pd.read_csv(report / 'benchmark.csv').set_index('model')
    batch = pd.read_parquet(root / p4['paths']['splits'] / 'validation.parquet').iloc[:16]
    checks = {}
    for family in chosen:
        recomputed = classification_metrics(predicted.label_id, predicted[family])
        if recomputed != metrics[family]['test']:
            raise ValueError('Saved prediction metrics differ')
        for key, value in flat_metrics(recomputed).items():
            if not np.isclose(benchmark.loc[family, key], value, rtol=1e-12, atol=1e-12):
                raise ValueError('Benchmark CSV differs from saved metrics')
        cm = pd.read_csv(report / f'{family}_confusion_matrix.csv', index_col=0)
        np.testing.assert_array_equal(cm.to_numpy(), recomputed['confusion_matrix'])
        artifact = load_classical(models / family, root)
        if artifact.metadata['model_sha256'] != lock['model_hashes'][family]:
            raise ValueError('Reloaded model differs from selection lock')
        result = artifact.predict(batch)
        if len(result) != len(batch) or any(row['confidence'] is not None or row['aspects'] for row in result):
            raise ValueError('Invalid overall inference output')
        checks[family] = 'PASS'
    return {'status': 'PASS', 'models': checks, 'saved_test_predictions': len(predicted),
            'selection_recomputed_from_validation': 'PASS', 'metrics_recomputed_from_saved_predictions': 'PASS',
            'test_predictions_rerun': False, 'input_hashes_verified': len(manifest['input_sha256'])}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, default=PROJECT_ROOT / 'reports/p5/p5_20261015')
    args = parser.parse_args()
    print(json.dumps(validate(args.report), indent=2))


if __name__ == '__main__':
    main()
