"""Đồ đạc P5 tổng hợp; điểm số ở đây không phải là bằng chứng đánh giá so sánh của dự án."""

import json
import shutil
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pytest
import sklearn
import yaml
from scipy import sparse

from scripts.train_p5 import error_diagnostics, run, validate_alignment, validate_isolation, write_json
from src.config import PROJECT_ROOT
from src.data.acquisition import sha256_file
from src.evaluation.classification import LABELS, classification_metrics
from src.preprocessing.english import ClassicalPreprocessor
from src.sentiment.classical import load_classical, make_estimator, select_candidate


def test_metrics_include_unpredicted_neutral_and_stable_mapping():
    result = classification_metrics([0, 1, 2], [2, 2, 2])
    assert result['macro_f1'] == pytest.approx(1 / 6)
    assert result['accuracy'] == pytest.approx(1 / 3)
    assert result['per_class']['neutral']['f1'] == 0
    assert result['confusion_matrix_order'] == list(LABELS)
    assert result['confusion_matrix'] == [[0, 0, 1]] * 3


@pytest.mark.parametrize('truth,prediction', [([], []), ([3], [0]), ([0], [1, 2]), ([[0]], [[0]])])
def test_metrics_reject_invalid_labels_and_shapes(truth, prediction):
    with pytest.raises(ValueError):
        classification_metrics(truth, prediction)


def test_selection_uses_validation_only_and_deterministic_ties():
    rows = [{'candidate_id': 'first', 'validation': {'macro_f1': .7},
             'test': {'macro_f1': .1}, 'convergence_warning': False},
            {'candidate_id': 'second', 'validation': {'macro_f1': .6},
             'test': {'macro_f1': .99}, 'convergence_warning': False}]
    assert select_candidate(rows)['candidate_id'] == 'first'
    rows[1]['validation']['macro_f1'] = .7
    assert select_candidate(rows)['candidate_id'] == 'first'
    rows[0]['convergence_warning'] = True
    assert select_candidate(rows)['candidate_id'] == 'second'
    rows[1]['convergence_warning'] = True
    with pytest.raises(ValueError):
        select_candidate(rows)


@pytest.mark.parametrize('family,params', [('majority', {}), ('logistic_regression', {'C': .5}),
    ('linear_svm', {'C': .5}), ('decision_tree', {'max_depth': 5, 'min_samples_leaf': 2})])
def test_sparse_fit_reproducible_serialization(tmp_path, family, params):
    matrix = sparse.csr_matrix(np.tile(np.eye(3), (4, 1)))
    labels = np.tile([0, 1, 2], 4)
    one, two = make_estimator(family, params, 42), make_estimator(family, params, 42)
    one.fit(matrix, labels)
    two.fit(matrix, labels)
    np.testing.assert_array_equal(one.predict(matrix), two.predict(matrix))
    joblib.dump(one, tmp_path / 'model.joblib')
    np.testing.assert_array_equal(one.predict(matrix), joblib.load(tmp_path / 'model.joblib').predict(matrix))


def test_tree_requires_overfit_controls():
    with pytest.raises(ValueError):
        make_estimator('decision_tree', {}, 42)


@pytest.fixture
def frozen_root(tmp_path):
    pre_dir, split_dir, report = [tmp_path / p for p in ('artifacts/pre', 'data/splits', 'reports/p4')]
    for directory in (pre_dir, split_dir, report, tmp_path / 'configs'):
        directory.mkdir(parents=True)
    frames = {}
    for split, n in (('train', 18), ('validation', 6), ('test', 9)):
        frames[split] = pd.DataFrame([{
            'review_id': f'{split}{i}', 'split': split, 'label_id': i % 3,
            'sentiment': LABELS[i % 3], 'label_provenance': 'rating-derived proxy',
            'text': f'{split} unique{i} ' + ('bad broken never works', 'okay average mixed quality', 'great excellent love laptop')[i % 3],
            'rating': [1, 3, 5][i % 3], 'parent_asin': f'{split}p{i}', 'asin': f'{split}a{i}',
            'split_group_id': f'{split}g{i}', 'clean_text_sha256': f'{split}h{i}', 'language': 'en'
        } for i in range(n)])
    pre = ClassicalPreprocessor(min_df=1)
    pre.fit_train(frames['train'])
    joblib.dump(pre, pre_dir / 'tfidf.joblib')
    for split, frame in frames.items():
        frame.to_parquet(split_dir / f'{split}.parquet', index=False)
        frame[['review_id', 'label_id', 'split']].to_parquet(pre_dir / f'{split}_feature_rows.parquet', index=False)
        sparse.save_npz(pre_dir / f'{split}_tfidf.npz', pre.transform(frame))
    source = tmp_path / 'data/source.parquet'
    pd.concat(frames.values()).to_parquet(source, index=False)
    write_json(report / 'input_preservation.json', {})
    write_json(report / 'environment.json', {'packages': {'scikit-learn': sklearn.__version__}})
    inputs = {p.relative_to(tmp_path).as_posix(): sha256_file(p)
              for directory in (pre_dir, split_dir) for p in directory.iterdir()}
    write_json(report / 'manifest.json', {'output_sha256': inputs, 'implementation_sha256': {},
               'source': 'data/source.parquet', 'source_sha256': sha256_file(source),
               'paths': {'preprocessing': 'artifacts/pre', 'splits': 'data/splits', 'report': 'reports/p4'}})
    cfg = yaml.safe_load((PROJECT_ROOT / 'configs/p5.yaml').read_text())
    cfg.update(p4_manifest='reports/p4/manifest.json', output_suffix='fixture')
    cfg['grids'] = {key: [values[0]] for key, values in cfg['grids'].items()}
    (tmp_path / 'configs/p5.yaml').write_text(yaml.safe_dump(cfg, sort_keys=False))
    for path in ('configs/model.yaml', 'scripts/train_p5.py', 'src/sentiment/classical.py', 'src/evaluation/classification.py'):
        destination = tmp_path / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(PROJECT_ROOT / path, destination)
    return tmp_path, frames


def test_alignment_rejects_reordered_targets_and_label_corruption(frozen_root):
    root, frames = frozen_root
    frame = frames['train']
    rows = frame[['review_id', 'label_id', 'split']]
    matrix = sparse.load_npz(root / 'artifacts/pre/train_tfidf.npz')
    validate_alignment(frame, rows, matrix, 'train')
    with pytest.raises(AssertionError):
        validate_alignment(frame, rows.iloc[::-1], matrix, 'train')
    frame.loc[0, 'sentiment'] = 'positive'
    with pytest.raises(ValueError, match='mapping'):
        validate_alignment(frame, rows, matrix, 'train')


def test_isolation_rejects_shared_products(frozen_root):
    _, frames = frozen_root
    validate_isolation(frames)
    frames['test'].loc[0, 'parent_asin'] = frames['train'].loc[0, 'parent_asin']
    with pytest.raises(ValueError, match='parent_asin'):
        validate_isolation(frames)


def test_full_fixture_run_freezes_selection_and_never_refits_preprocessing(frozen_root, monkeypatch):
    root, frames = frozen_root
    def forbidden(*args, **kwargs):
        raise AssertionError('Preprocessing must not be fitted during P5')
    monkeypatch.setattr(ClassicalPreprocessor, 'fit_train', forbidden)
    import scripts.train_p5 as runner
    real_make = runner.make_estimator
    fits = []
    def tracked_make(*args):
        estimator = real_make(*args)
        original_fit = estimator.fit
        def fit(x, y):
            assert x.shape[0] == len(frames['train'])
            np.testing.assert_array_equal(y, frames['train'].label_id)
            fits.append(len(y))
            return original_fit(x, y)
        estimator.fit = fit
        # Việc đóng phiên bản chỉ là gián điệp kiểm thử; loại bỏ trước khi tuần tự hóa.
        def cleaned_fit(x, y):
            result = fit(x, y)
            del estimator.fit
            return result
        estimator.fit = cleaned_fit
        return estimator
    monkeypatch.setattr(runner, 'make_estimator', tracked_make)
    result = run(root / 'configs/p5.yaml', root)
    assert result['status'] == 'DONE' and fits == [18] * 4
    report = root / 'reports/p5/fixture'
    assert json.loads((report / 'validation.json').read_text())['test_used_for_selection'] is False
    predictions = pd.read_parquet(root / 'artifacts/models/fixture/test_predictions.parquet')
    assert len(predictions) == 9
    from scripts.validate_p5 import validate
    audit = validate(report, root)
    assert audit['status'] == 'PASS' and audit['test_predictions_rerun'] is False
    artifact = load_classical(root / 'artifacts/models/fixture/linear_svm', root)
    output = artifact.predict(pd.DataFrame({'text': ['not good'], 'language': ['en'], 'rating': [5]}))
    assert output[0]['sentiment'] in LABELS and output[0]['confidence'] is None
    assert output[0]['aspects'] == []
    with pytest.raises(ValueError):
        artifact.predict(pd.DataFrame({'text': ['not good'], 'language': ['vi']}))
    with pytest.raises(ValueError):
        artifact.predict(pd.DataFrame({'text': ['']}))
    with pytest.raises(FileExistsError):
        run(root / 'configs/p5.yaml', root)
    with (root / 'artifacts/pre/tfidf.joblib').open('ab') as handle:
        handle.write(b'changed')
    with pytest.raises(ValueError, match='preprocessing'):
        load_classical(root / 'artifacts/models/fixture/linear_svm', root)


def test_error_queue_is_diagnostic_and_handles_zero_errors(frozen_root):
    _, frames = frozen_root
    report, queue = error_diagnostics(frames['test'], frames['test'].label_id.to_numpy(), 42)
    assert report['errors'] == 0 and queue.empty
    assert report['sarcasm_and_true_rating_text_disagreement'].startswith('NOT_MEASURED')
