"""Đối chiếu artifacts/selection/metrics đã lưu; không dự đoán test lần nữa."""

import argparse
import json

import numpy as np
import pandas as pd

from scripts.revalidate_model_data import write_json
from scripts.train_modern import latest_report
from src.config import PROJECT_ROOT
from src.data.acquisition import sha256_file
from src.evaluation.classification import classification_metrics
from src.preprocessing.semantic_cache import cache_identity, load_semantic_config


def validate(experiment: str) -> dict:
    root = PROJECT_ROOT
    cfg = load_semantic_config(root)
    report = latest_report(root / cfg['reports'] / experiment)
    artifact = root / cfg['experiments'] / experiment
    result = json.loads((report / 'result.json').read_text(encoding='utf-8'))
    artifact = root / result.get('artifact_directory', f'{cfg["experiments"]}/{experiment}')
    if result['status'] != 'PASS':
        raise ValueError('Experiment chưa PASS')
    lock = json.loads((report / 'selection_lock.json').read_text(encoding='utf-8'))
    if lock['cache_identity'] != cache_identity(cfg, root):
        raise ValueError('Dữ liệu/config thay đổi')
    for name, digest in lock['model_sha256'].items():
        if sha256_file(artifact / name) != digest:
            raise ValueError('Artifact thay đổi sau selection lock')
    candidates = json.loads((report / 'candidates.json').read_text(encoding='utf-8'))['candidates']
    best = max(candidates, key=lambda row: row['validation_metrics']['macro_f1'])
    if lock['selected_spec'] != best['spec'] or lock['validation_macro_f1'] != best['validation_metrics']['macro_f1']:
        raise ValueError('Lựa chọn không khớp validation')
    recomputed = {}
    for split in ['validation', 'test']:
        frame = pd.read_parquet(root / cfg['splits'] / f'{split}.parquet')
        predictions = pd.read_parquet(report / f'{split}_predictions.parquet')
        if frame.review_id.tolist() != predictions.review_id.tolist() or frame.label_id.tolist() != predictions.label_id.tolist():
            raise ValueError('Sai ID/label alignment dự đoán')
        predicted = predictions.prediction_id.to_numpy()
        if not np.array_equal(predicted, np.load(report / f'{split}_predictions.npy')):
            raise ValueError('Prediction NPY khác parquet')
        observed = classification_metrics(predictions.label_id, predicted)
        observed['balanced_accuracy'] = float(np.mean([v['recall'] for v in observed['per_class'].values()]))
        expected = json.loads((report / f'{split}_metrics.json').read_text(encoding='utf-8'))
        if expected != observed:
            raise ValueError('Metrics khác dự đoán đã lưu')
        recomputed[split] = 'PASS'
    if not lock['selection_complete_before_test']:
        raise ValueError('Không có selection lock trước test')
    summary = {'status': 'PASS', 'experiment': experiment, 'metrics_recomputed': recomputed,
               'artifact_hashes': 'PASS', 'validation_selection': 'PASS', 'test_predictions_rerun': False}
    write_json(report / 'independent_validation.json', summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('experiment')
    args = parser.parse_args()
    print(json.dumps(validate(args.experiment)))


if __name__ == '__main__':
    main()
