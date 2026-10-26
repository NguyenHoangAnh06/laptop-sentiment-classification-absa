"""Nghiệm thu artifacts thật của P7; không suy luận lại hoặc huấn luyện mô hình."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.config import PROJECT_ROOT
from src.evaluation.classification import classification_metrics


@pytest.fixture
def completed():
    file = PROJECT_ROOT / 'reports/p7_completion.json'
    if not file.exists():
        pytest.skip('P7 chưa chạy; không tuyên bố nghiệm thu artifacts cuối')
    return json.loads(file.read_text(encoding='utf-8'))


def test_final_selection_uses_validation_and_all_models(completed):
    table = pd.read_csv(PROJECT_ROOT / 'reports/p7_unified_results.csv')
    assert len(table) == 6 and len(set(table.model)) == 6
    expected = table.loc[table.validation_macro_f1.idxmax(), 'model']
    assert completed['selected_by_validation'] == expected
    assert completed['test_tuning'] is False and completed['predictions_rerun'] is False
    for name in ['E03_tabpfn_v3_embedding', 'E04_tabpfn_v35_embedding']:
        source = completed.get('model_sources', {}).get(name)
        row = table.set_index('model').loc[name]
        if source:
            assert source['status'] == 'SUCCESS' and source['kind'] == 'kaggle_csv'
            assert row.data_regime == 'FULL' and row.train_samples == 21000
        else:
            assert row.data_regime == 'SUBSAMPLED'


def test_final_predictions_and_metrics_are_aligned(completed):
    table = pd.read_csv(PROJECT_ROOT / 'reports/p7_unified_results.csv')
    for name in completed['models']:
        cloud = completed.get('model_sources', {}).get(name)
        if cloud:
            folder = PROJECT_ROOT / cloud['directory']
            metadata = json.loads((folder / 'run_metadata.json').read_text(encoding='utf-8'))
            assert metadata['status'] == 'PASS' and metadata['train_count'] == 21000
            for split in ['validation', 'test']:
                source = pd.read_parquet(PROJECT_ROOT / 'data/processed/splits/p4_20261009_final' / f'{split}.parquet')
                prediction = pd.read_csv(folder / f'{split}_predictions.csv')
                assert source.review_id.tolist() == prediction.review_id.tolist()
                assert source.label_id.tolist() == prediction.y_true.tolist()
                metrics = classification_metrics(prediction.y_true, prediction.y_pred)
                saved = json.loads((folder / f'{split}_metrics.json').read_text(encoding='utf-8'))
                for key in metrics:
                    assert metrics[key] == saved[key]
                if split == 'test':
                    assert np.isclose(table.set_index('model').loc[name, 'macro_f1'], metrics['macro_f1'], atol=1e-14)
            continue
        folder = PROJECT_ROOT / 'reports/semantic_20261024' / name
        if (folder / 'latest_attempt.json').exists():
            folder /= 'attempts/' + json.loads((folder / 'latest_attempt.json').read_text(encoding='utf-8'))['attempt']
        assert json.loads((folder / 'independent_validation.json').read_text(encoding='utf-8'))['status'] == 'PASS'
        result = json.loads((folder / 'result.json').read_text(encoding='utf-8'))
        assert (PROJECT_ROOT / result.get('artifact_directory', 'artifacts/models/semantic_20261024/' + name)).is_dir()
        for split in ['validation', 'test']:
            source = pd.read_parquet(PROJECT_ROOT / 'data/processed/splits/p4_20261009_final' / f'{split}.parquet')
            prediction = pd.read_parquet(folder / f'{split}_predictions.parquet')
            assert source.review_id.tolist() == prediction.review_id.tolist()
            assert source.label_id.tolist() == prediction.label_id.tolist()
            metrics = classification_metrics(prediction.label_id, prediction.prediction_id)
            assert sum(map(sum, metrics['confusion_matrix'])) == len(source)
            saved = json.loads((folder / f'{split}_metrics.json').read_text(encoding='utf-8'))
            for key in metrics:
                assert saved[key] == metrics[key]
            if split == 'test':
                assert np.isclose(table.set_index('model').loc[name, 'macro_f1'], metrics['macro_f1'], atol=1e-14)


def test_final_tabpfn_versions_are_distinct(completed):
    versions = json.loads((PROJECT_ROOT / 'reports/tabpfn_version_verification.json').read_text(encoding='utf-8'))
    assert versions['E03']['requested_version'] == versions['E03']['resolved_version'] == 'V3'
    assert versions['E04']['requested_version'] == versions['E04']['resolved_version'] == 'V3_5'
    assert Path(versions['E03']['checkpoint']).name != Path(versions['E04']['checkpoint']).name


def test_error_examples_are_not_human_gold(completed):
    errors = pd.read_csv(PROJECT_ROOT / 'reports/p7_error_examples.csv')
    assert errors.human_verified.eq(False).all()
    assert errors.confidence.isna().all()
    assert errors.star_text_mismatch.str.startswith('PENDING').all()
