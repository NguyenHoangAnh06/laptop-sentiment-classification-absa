"""Tính lại metrics từ dự đoán P6 đã lưu và đối chiếu lựa chọn validation."""

import json
import numpy as np
import pandas as pd

from scripts.revalidate_model_data import write_json
from scripts.train_modern import metrics
from src.config import PROJECT_ROOT
from src.data.acquisition import sha256_file
from src.preprocessing.semantic_cache import cache_identity, load_semantic_config


def validate():
    root = PROJECT_ROOT
    cfg = load_semantic_config()
    report = root / cfg['reports'] / 'E05_transformer'
    result = json.loads((report / 'result.json').read_text(encoding='utf-8'))
    lock = json.loads((report / 'selection_lock.json').read_text(encoding='utf-8'))
    assert result['status'] == 'PASS'
    assert lock['cache_identity'] == cache_identity(cfg)
    assert lock['selection_complete_before_test'] and result['test_prediction_passes'] == 1
    assert lock['selected'] == max(lock['candidates'], key=lambda c: c['validation_macro_f1'])
    assert lock['checkpoint_sha256'] == sha256_file(root / result['artifact_directory'] / 'model.safetensors')
    history = json.loads((report / 'history.json').read_text(encoding='utf-8'))
    for candidate in lock['candidates']:
        assert candidate['validation_macro_f1'] == max(r['validation']['macro_f1'] for r in history
                                                     if r['mode'] == candidate['spec']['mode'])
    for split in ['validation', 'test']:
        frame = pd.read_parquet(root / cfg['splits'] / f'{split}.parquet')
        pred = pd.read_parquet(report / f'{split}_predictions.parquet')
        assert frame.review_id.tolist() == pred.review_id.tolist()
        assert frame.label_id.tolist() == pred.label_id.tolist()
        np.testing.assert_array_equal(pred.prediction_id, np.load(report / f'{split}_predictions.npy'))
        assert metrics(pred.label_id, pred.prediction_id) == json.loads((report / f'{split}_metrics.json').read_text(encoding='utf-8'))
    summary = {'status': 'PASS', 'prediction_alignment': 'PASS', 'metrics_recomputed': 'PASS',
               'validation_selection': 'PASS', 'checkpoint_hash': 'PASS', 'test_predictions_rerun': False}
    write_json(report / 'independent_validation.json', summary)
    print(json.dumps(summary))


if __name__ == '__main__':
    validate()
