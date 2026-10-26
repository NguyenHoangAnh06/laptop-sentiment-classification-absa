"""P5 đánh giá so sánh có thể tái tạo trên đã cố định P4 đặc trưng; không bao giờ xử lý trước khớp mô hình."""

import argparse
import importlib.metadata
import json
import platform
import re
import sys
import time
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
import yaml
from scipy import sparse
from sklearn.exceptions import ConvergenceWarning
from threadpoolctl import threadpool_limits

from src.config import PROJECT_ROOT, load_config
from src.data.acquisition import sha256_file
from src.evaluation.classification import LABELS, ResourceMonitor, classification_metrics, flat_metrics
from src.preprocessing.english import ordered_id_digest
from src.sentiment.classical import load_classical, make_estimator, select_candidate

SPLITS = ('train', 'validation', 'test')


def write_json(path: Path, value: dict | list) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')


def validate_alignment(frame: pd.DataFrame, rows: pd.DataFrame, matrix, split: str) -> None:
    """Loại bỏ các lỗi label/order/split trước khi điều chỉnh hoặc đánh giá công cụ ước tính."""
    expected = frame[['review_id', 'label_id', 'split']].reset_index(drop=True)
    pd.testing.assert_frame_equal(rows.reset_index(drop=True), expected)
    if frame.empty or not frame['split'].eq(split).all() or frame.review_id.duplicated().any():
        raise ValueError('Invalid split membership')
    if not pd.api.types.is_integer_dtype(frame.label_id) or set(frame.label_id) != {0, 1, 2}:
        raise ValueError('All three integer label IDs required')
    if frame.sentiment.tolist() != [LABELS[i] for i in frame.label_id]:
        raise ValueError('Label mapping mismatch')
    if not frame.label_provenance.eq('rating-derived proxy').all():
        raise ValueError('Unexpected target provenance')
    if not sparse.isspmatrix_csr(matrix) or matrix.shape[0] != len(frame):
        raise ValueError('Aligned CSR features required')
    if not np.isfinite(matrix.data).all():
        raise ValueError('Nonfinite features')


def validate_isolation(frames: dict) -> dict:
    """Kiểm tra lại thành phần cố định membership/product/text tách rời, không tách rời."""
    checks = {}
    for column in ('review_id', 'parent_asin', 'asin', 'split_group_id', 'text', 'clean_text_sha256'):
        sets = {split: set(frame[column].dropna()) for split, frame in frames.items()}
        checks[column] = {}
        for i, left in enumerate(SPLITS):
            for right in SPLITS[i + 1:]:
                count = len(sets[left] & sets[right])
                checks[column][f'{left}__{right}'] = count
                if count:
                    raise ValueError(f'Cross-split overlap: {column}')
    return checks


def protected_inputs(root: Path, manifest: dict) -> dict:
    """Liên kết các đầu vào đã cố định hiện tại với bằng chứng trước đó, bao gồm các ảnh chụp nhanh P0–P3."""
    expected = dict(manifest['output_sha256'])
    expected.update(manifest['implementation_sha256'])
    expected[manifest['source']] = manifest['source_sha256']
    snapshot = root / manifest['paths']['report'] / 'input_preservation.json'
    expected.update(json.loads(snapshot.read_text(encoding='utf-8')))
    for relative, digest in expected.items():
        if sha256_file(root / relative) != digest:
            raise ValueError(f'Frozen input differs from P4 evidence: {relative}')
    return expected


def load_inputs(root: Path, manifest: dict) -> tuple:
    """Tải các tập đã chia bất biến theo thứ tự sidecar và xác minh tất cả các biến đổi đã cố định."""
    pre_dir = root / manifest['paths']['preprocessing']
    preprocessor = joblib.load(pre_dir / 'tfidf.joblib')
    frames, matrices = {}, {}
    for split in SPLITS:
        frame = pd.read_parquet(root / manifest['paths']['splits'] / f'{split}.parquet')
        rows = pd.read_parquet(pre_dir / f'{split}_feature_rows.parquet')
        matrix = sparse.load_npz(pre_dir / f'{split}_tfidf.npz')
        validate_alignment(frame, rows, matrix, split)
        transformed = preprocessor.transform(frame)
        if matrix.shape != transformed.shape or (matrix != transformed).nnz:
            raise ValueError(f'Frozen TF-IDF mismatch: {split}')
        frames[split], matrices[split] = frame, matrix
    if preprocessor.fit_id_sha256 != ordered_id_digest(frames['train'].review_id.tolist()):
        raise ValueError('Preprocessing fit IDs differ from train IDs')
    if preprocessor.fit_rows != len(frames['train']):
        raise ValueError('Preprocessing fit row count differs')
    frequency = np.asarray((matrices['train'] > 0).sum(axis=0)).ravel()
    expected_idf = np.log((1 + len(frames['train'])) / (1 + frequency)) + 1
    if not np.allclose(expected_idf, preprocessor.vectorizer.idf_, rtol=1e-6, atol=1e-6):
        raise ValueError('IDF not consistent with train-only document frequency')
    return frames, matrices, preprocessor


def error_diagnostics(frame: pd.DataFrame, predicted: np.ndarray, seed: int) -> tuple:
    """Các lát mô tả và hàng đợi chẩn đoán; cờ heuristic không phải là nhãn gán."""
    data = frame[['review_id', 'text', 'label_id', 'rating']].copy()
    data['prediction_id'] = predicted
    data['error'] = data.label_id.ne(data.prediction_id)
    lengths = data.text.str.split().str.len()
    text = data.text.str.lower()
    data['negation_cue'] = text.str.contains(r"\b(?:not|never|no|cannot)\b|n't", regex=True)
    data['mixed_lexical_cues'] = text.str.contains(r'\b(?:good|great|love|excellent)\b') & text.str.contains(
        r'\b(?:bad|poor|broken|terrible|hate)\b')
    data['short_le_5_words'] = lengths.le(5)
    data['long_gt_200_words'] = lengths.gt(200)
    slices = {}
    for flag in ('negation_cue', 'mixed_lexical_cues', 'short_le_5_words', 'long_gt_200_words'):
        mask = data[flag]
        slices[flag] = {'rows': int(mask.sum()), 'errors': int(data.loc[mask, 'error'].sum()),
                        'error_rate': float(data.loc[mask, 'error'].mean()) if mask.any() else None}
    samples = []
    errors = data[data.error]
    for _, group in errors.groupby(['label_id', 'prediction_id'], sort=True):
        samples.append(group.sample(n=min(5, len(group)), random_state=seed))
    for flag in slices:
        group = errors[errors[flag]]
        if len(group):
            samples.append(group.sample(n=min(3, len(group)), random_state=seed))
    queue = pd.concat(samples).drop_duplicates('review_id') if samples else errors
    return {'slices': slices, 'errors': int(data.error.sum()), 'total': len(data),
            'review_queue_rows': len(queue), 'annotation_status': 'UNANNOTATED diagnostic queue',
            'sarcasm_and_true_rating_text_disagreement': 'NOT_MEASURED; human annotation required',
            'flags': 'Fixed lexical/length diagnostics, not confirmed semantic phenomena'}, queue


def run(config_path: Path, root: Path = PROJECT_ROOT) -> dict:
    """Train/tune trên lựa chọn khóa train/validation,, sau đó đánh giá cố định kiểm thử một lần."""
    cfg = yaml.safe_load(config_path.read_text(encoding='utf-8'))
    suffix = cfg['output_suffix']
    if not re.fullmatch(r'[A-Za-z0-9_-]+', suffix):
        raise ValueError('Invalid output suffix')
    model_dir, report_dir = root / 'artifacts/models' / suffix, root / 'reports/p5' / suffix
    if model_dir.exists() or report_dir.exists():
        raise FileExistsError('Use a fresh output_suffix; completed or partial runs are never overwritten')
    if list(cfg['grids']) != ['majority', 'logistic_regression', 'linear_svm', 'decision_tree']:
        raise ValueError('All four P5 families required in fixed declared order')
    if load_config('model', root)['label_to_id'] != dict(zip(LABELS, range(3))):
        raise ValueError('Project label mapping changed')
    manifest_path = root / cfg['p4_manifest']
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    environment = json.loads((root / manifest['paths']['report'] / 'environment.json').read_text(encoding='utf-8'))
    if environment['packages']['scikit-learn'] != sklearn.__version__:
        raise ValueError('Use the P4 environment: .venv/Scripts/python.exe')
    model_dir.mkdir(parents=True)
    report_dir.mkdir(parents=True)
    started = time.perf_counter()
    def guard():
        import psutil
        if time.perf_counter() - started > cfg['max_seconds']:
            raise RuntimeError('Time budget exceeded between operations')
        if psutil.Process().memory_info().rss > cfg['max_memory_bytes']:
            raise RuntimeError('RSS budget exceeded between operations')
    try:
        with ResourceMonitor() as total, threadpool_limits(limits=cfg['threads']):
            protected = protected_inputs(root, manifest)
            protected[cfg['p4_manifest']] = sha256_file(manifest_path)
            frames, matrices, preprocessor = load_inputs(root, manifest)
            isolation = validate_isolation(frames)
            write_json(report_dir / 'input_validation.json', {
                'status': 'PASS', 'isolation': isolation, 'train_only_idf_reconstruction': 'PASS',
                'frozen_tfidf_full_retransform': 'PASS', 'protected_input_count': len(protected),
                'counts': {s: {'rows': len(f), 'products': f.parent_asin.nunique(),
                               'labels': {LABELS[i]: int(f.label_id.eq(i).sum()) for i in range(3)}}
                           for s, f in frames.items()},
                'near_duplicate_evidence': 'Reused checksum-bound P4 report; not exhaustive semantic proof'})
            guard()
            write_json(report_dir / 'config.json', cfg)
            write_json(report_dir / 'environment.json', {
                'python': sys.version, 'platform': platform.platform(), 'threads': cfg['threads'],
                'device': 'CPU; no P6/GPU training',
                'packages': {p: importlib.metadata.version(p) for p in
                             ('scikit-learn', 'scipy', 'numpy', 'pandas', 'pyarrow', 'joblib', 'psutil', 'threadpoolctl')},
                'resource_method': '20ms whole-process RSS sampling; operation-boundary soft limits',
                'selection_protocol': 'Validation macro F1; exact ties follow grid order; no train+validation refit',
                'imbalance_rationale': 'Compare None vs balanced on validation, train-derived weights; no resampling',
                'latency_protocol': 'First fixed validation batch, one warmup, median repeated batch latency/row'})
            candidates, selected = [], {}
            pre_path = root / manifest['paths']['preprocessing'] / 'tfidf.joblib'
            for family, grid in cfg['grids'].items():
                fitted, family_rows = {}, []
                for index, params in enumerate(grid):
                    guard()
                    candidate_id = f'{family}_{index:02d}'
                    estimator = make_estimator(family, params, cfg['seed'])
                    with warnings.catch_warnings(record=True) as caught, ResourceMonitor() as resources:
                        warnings.simplefilter('always')
                        estimator.fit(matrices['train'], frames['train'].label_id.to_numpy())
                    if resources.peak_rss_bytes > cfg['max_memory_bytes']:
                        raise RuntimeError('Sampled training RSS budget exceeded')
                    train_metrics = classification_metrics(frames['train'].label_id, estimator.predict(matrices['train']))
                    val_metrics = classification_metrics(frames['validation'].label_id, estimator.predict(matrices['validation']))
                    row = {'candidate_id': candidate_id, 'family': family, 'params': params,
                           'training_seconds': resources.seconds, 'peak_process_rss_bytes': resources.peak_rss_bytes,
                           'warnings': [str(w.message) for w in caught],
                           'convergence_warning': any(issubclass(w.category, ConvergenceWarning) for w in caught),
                           'train': train_metrics, 'validation': val_metrics}
                    candidates.append(row)
                    family_rows.append(row)
                    fitted[candidate_id] = estimator
                    write_json(report_dir / 'training_history.json', candidates)
                    print(f'{candidate_id}: val macro_f1={val_metrics["macro_f1"]:.6f}, fit={resources.seconds:.2f}s', flush=True)
                best = select_candidate(family_rows)
                selected[family] = best
                directory = model_dir / family
                directory.mkdir()
                joblib.dump(fitted[best['candidate_id']], directory / 'model.joblib', compress=3)
                write_json(directory / 'metadata.json', {
                    'family': family, 'candidate_id': best['candidate_id'], 'params': best['params'],
                    'seed': cfg['seed'], 'label_to_id': dict(zip(LABELS, range(3))),
                    'feature_allowlist': ['text'], 'label_provenance': 'rating-derived proxy',
                    'preprocessor_path': pre_path.relative_to(root).as_posix(),
                    'preprocessor_sha256': sha256_file(pre_path),
                    'model_sha256': sha256_file(directory / 'model.joblib'),
                    'sklearn_version': sklearn.__version__, 'fit_split': 'train',
                    'fit_ids_sha256': ordered_id_digest(frames['train'].review_id.tolist()),
                    'selection_split': 'validation', 'confidence': None, 'absa_implemented': False})
                del fitted
            winner = select_candidate(list(selected.values()))
            lock = {'selection_metric': 'validation macro_f1', 'tie_policy': 'declared grid/family order',
                    'winner': winner['family'], 'selected_candidates': selected,
                    'no_refit_on_validation': True, 'test_prediction_passes_planned': 1,
                    'p4_manifest_sha256': sha256_file(manifest_path),
                    'config_sha256': sha256_file(config_path),
                    'model_hashes': {f: sha256_file(model_dir / f / 'model.joblib') for f in selected}}
            write_json(report_dir / 'selection_lock.json', lock)
            lock_digest = sha256_file(report_dir / 'selection_lock.json')
            # Chỉ khối này truy cập các mục tiêu kiểm thử để đánh giá bộ phân loại.
            benchmark, all_metrics, predictions, reload_checks = [], {}, frames['test'][['review_id', 'label_id']].copy(), {}
            for family, choice in selected.items():
                guard()
                artifact = load_classical(model_dir / family, root)
                estimator = artifact.estimator
                with ResourceMonitor() as test_resources:
                    predicted = estimator.predict(matrices['test']).astype(int)
                metrics = classification_metrics(frames['test'].label_id, predicted)
                all_metrics[family] = {'validation': choice['validation'], 'test': metrics}
                predictions[family] = predicted
                batch = frames['validation'].iloc[:cfg['latency_batch_size']]
                expected = estimator.predict(matrices['validation'][:len(batch)])
                np.testing.assert_array_equal(artifact.predict_ids(batch), expected)
                times = []
                with ResourceMonitor() as latency_resources:
                    for _ in range(cfg['latency_repeats']):
                        tick = time.perf_counter()
                        np.testing.assert_array_equal(artifact.predict_ids(batch), expected)
                        times.append(time.perf_counter() - tick)
                reload_checks[family] = 'PASS: raw-text validation batch equals saved feature prediction'
                model_bytes = (model_dir / family / 'model.joblib').stat().st_size
                row = {'model': family, 'selected_by_validation': family == winner['family'],
                       'validation_macro_f1': choice['validation']['macro_f1'], **flat_metrics(metrics),
                       'training_seconds': choice['training_seconds'],
                       'search_training_seconds': sum(r['training_seconds'] for r in candidates if r['family'] == family),
                       'test_prediction_seconds': test_resources.seconds,
                       'inference_latency_ms_per_review': float(np.median(times) * 1000 / len(batch)),
                       'latency_batch_size': len(batch), 'latency_repeats': len(times),
                       'model_bytes': model_bytes, 'shared_preprocessor_bytes': pre_path.stat().st_size,
                       'inference_artifact_bytes': model_bytes + pre_path.stat().st_size,
                       'peak_process_rss_bytes': max(choice['peak_process_rss_bytes'], test_resources.peak_rss_bytes,
                                                     latency_resources.peak_rss_bytes)}
                benchmark.append(row)
                pd.DataFrame(metrics['confusion_matrix'], index=LABELS, columns=LABELS).rename_axis('true_label').to_csv(
                    report_dir / f'{family}_confusion_matrix.csv')
                pd.DataFrame(choice['validation']['confusion_matrix'], index=LABELS, columns=LABELS).rename_axis('true_label').to_csv(
                    report_dir / f'{family}_validation_confusion_matrix.csv')
            predictions.to_parquet(model_dir / 'test_predictions.parquet', index=False)
            pd.DataFrame(benchmark).to_csv(report_dir / 'benchmark.csv', index=False)
            write_json(report_dir / 'metrics.json', all_metrics)
            diagnostics, queue = error_diagnostics(frames['test'], predictions[winner['family']].to_numpy(), cfg['seed'])
            queue.to_parquet(model_dir / 'error_review_queue.parquet', index=False)
            write_json(report_dir / 'error_analysis.json', diagnostics)
            if lock_digest != sha256_file(report_dir / 'selection_lock.json'):
                raise ValueError('Selection lock changed after test evaluation')
            for relative, digest in protected.items():
                if sha256_file(root / relative) != digest:
                    raise ValueError(f'Protected input changed during P5: {relative}')
            guard()
            footprint = sum(p.stat().st_size for d in (model_dir, report_dir) for p in d.rglob('*') if p.is_file())
            if footprint > cfg['max_output_bytes']:
                raise RuntimeError('Output budget exceeded')
            write_json(report_dir / 'validation.json', {'status': 'PASS', 'reload_checks': reload_checks,
                       'protected_inputs_unchanged': len(protected), 'selection_lock_sha256': lock_digest,
                       'test_prediction_passes_per_family': 1, 'test_used_for_selection': False,
                       'output_bytes_before_manifest': footprint})
        if total.peak_rss_bytes > cfg['max_memory_bytes']:
            raise RuntimeError('Whole-run sampled RSS budget exceeded')
        hashes = {p.relative_to(root).as_posix(): sha256_file(p) for d in (model_dir, report_dir)
                  for p in d.rglob('*') if p.is_file()}
        result = {'status': 'DONE', 'phase': 'P5', 'winner': winner['family'],
                  'runtime_seconds': total.seconds, 'peak_process_rss_bytes': total.peak_rss_bytes,
                  'p4_manifest': cfg['p4_manifest'], 'selection_lock_sha256': lock_digest,
                  'input_sha256': protected, 'output_sha256': hashes,
                  'implementation_sha256': {p: sha256_file(root / p) for p in
                      ('scripts/train_p5.py', 'src/sentiment/classical.py', 'src/evaluation/classification.py', 'configs/p5.yaml')},
                  'limitations': ['laptop-only findings', 'rating-derived proxy-label noise',
                                 'SemEval-to-Amazon platform/style shift within laptop reviews',
                                 'small manually annotated gold set (not yet available)'],
                  'bert': 'P6 NOT RUN; outside official P5 scope', 'gold_labels_created': False}
        write_json(report_dir / 'manifest.json', result)
        return result
    except Exception as exc:
        write_json(report_dir / 'status.json', {'status': 'BLOCKED', 'BLOCKED': str(exc),
                   'NEXT_ACTION': 'Resolve failure, inspect partial evidence, use a fresh suffix; do not retune from test'})
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=PROJECT_ROOT / 'configs/p5.yaml')
    args = parser.parse_args()
    result = run(args.config)
    print(json.dumps({k: result[k] for k in ('status', 'winner', 'runtime_seconds', 'peak_process_rss_bytes')}))


if __name__ == '__main__':
    main()
