"""P5 theo từng experiment, tái sử dụng cache và khóa selection trước test."""

import argparse
import gc
import importlib.metadata
import json
import os
import re
import time
from pathlib import Path

os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG', ':4096:8')
os.environ.setdefault('TABPFN_NO_BROWSER', '1')

import joblib
import numpy as np
import pandas as pd
import torch
import yaml

from scripts.revalidate_model_data import write_json
from src.config import PROJECT_ROOT
from src.data.acquisition import sha256_file
from src.evaluation.classification import ResourceMonitor, classification_metrics, flat_metrics
from src.preprocessing.semantic import ordered_digest
from src.preprocessing.semantic_cache import load_cache, load_semantic_config
from src.sentiment.bert import seed_everything
from src.sentiment.modern import balanced_weights, tabm_predict, train_tabm
from src.sentiment.tabpfn_versions import VERSIONS, make_tabpfn

ORDER = ['E00_majority', 'E01_xgboost_embedding', 'E02_tabm_embedding',
         'E03_tabpfn_v3_embedding', 'E04_tabpfn_v35_embedding']


def metrics(y, prediction):
    values = classification_metrics(y, prediction)
    values['balanced_accuracy'] = float(np.mean([v['recall'] for v in values['per_class'].values()]))
    return values


def latest_report(base: Path) -> Path:
    """Theo con trỏ attempt; chỉ nhận tên an toàn dưới cùng experiment."""
    pointer = base / 'latest_attempt.json'
    if not pointer.is_file():
        return base
    attempt = json.loads(pointer.read_text(encoding='utf-8'))['attempt']
    if not re.fullmatch(r'[A-Za-z0-9_-]+', attempt):
        raise ValueError('Tên attempt không hợp lệ')
    return base / 'attempts' / attempt


def run(experiment: str, *, attempt: str | None = None, train_samples: int | None = None) -> dict:
    root = PROJECT_ROOT
    cfg = load_semantic_config()
    train_cfg = yaml.safe_load((root / 'configs/modern_tabular.yaml').read_text(encoding='utf-8'))
    if not (root / 'reports/p4_semantic_independent_validation.json').is_file():
        raise ValueError('P4 chưa được xác minh độc lập')
    output = root / cfg['experiments'] / experiment
    report_dir = root / cfg['reports'] / experiment
    base_report = report_dir
    if attempt is not None:
        if not re.fullmatch(r'[A-Za-z0-9_-]+', attempt):
            raise ValueError('Tên attempt chỉ gồm chữ/số/_/-')
        previous_attempt = latest_report(base_report)
        old_result = json.loads((previous_attempt / 'result.json').read_text(encoding='utf-8'))
        if (old_result['status'] not in ('FAILED', 'BLOCKED')
                or (previous_attempt / 'selection_lock.json').exists()
                or (previous_attempt / 'test_predictions.npy').exists()):
            raise ValueError('Chỉ retry attempt bị chặn/thất bại trước selection/test; không tái đánh giá test')
        output = output / 'attempts' / attempt
        report_dir = report_dir / 'attempts' / attempt
    for previous in ORDER[:ORDER.index(experiment)]:
        previous_path = latest_report(root / cfg['reports'] / previous) / 'result.json'
        if not previous_path.is_file() or json.loads(previous_path.read_text(encoding='utf-8'))['status'] != 'PASS':
            raise ValueError(f'Experiment trước chưa PASS: {previous}')
    if output.exists() or report_dir.exists():
        raise ValueError('Đầu ra đã tồn tại; không overwrite model/kết quả/test lock')
    data, metadata = load_cache(cfg)
    # Test labels không được truyền cho fit/tuning; chỉ đọc sau khi selection lock đã ghi.
    test_frame = data.pop('test')['frame']
    train_x, train_y = data['train']['X'], data['train']['y']
    full_train_rows = len(train_y)
    if experiment in VERSIONS:
        # Cấu hình tài nguyên đo bằng train-only, không thay cấu hình E00/E01/E02.
        version = VERSIONS[experiment]
        assessment = root / 'reports/tabpfn_resources_20261024' / version / 'decision.json'
        decision = json.loads(assessment.read_text(encoding='utf-8'))
        if decision['status'] != 'PASS':
            raise ValueError('Resource assessment chưa PASS')
        effective_samples = full_train_rows if train_samples is None else train_samples
        if effective_samples != decision['train_samples']:
            raise ValueError('Số mẫu không khớp resource decision đã được đo')
        train_cfg['tabpfn']['prediction_batch_size'] = decision['prediction_batch_size']
        train_cfg['tabpfn']['fit_mode'] = decision['fit_mode']
    if train_samples is not None:
        if experiment not in VERSIONS:
            raise ValueError('Subsample chỉ được phép cho TabPFN sau resource assessment')
        from scripts.assess_tabpfn import stratified_ids
        chosen = stratified_ids(train_y, train_samples, train_cfg['seed'])
        train_x, train_y = np.array(train_x[chosen]), train_y[chosen]
    else:
        chosen = np.arange(len(train_y))
    val_x, val_y = data['validation']['X'], data['validation']['y']
    output.mkdir(parents=True)
    report_dir.mkdir(parents=True)
    seed_everything(train_cfg['seed'])
    torch.set_num_threads(train_cfg['threads'])
    torch.cuda.reset_peak_memory_stats()
    versions = {p: importlib.metadata.version(p) for p in ['torch', 'xgboost', 'tabm', 'tabpfn', 'numpy', 'scikit-learn']}
    provenance = {'experiment': experiment, 'attempt': attempt,
                  'artifact_directory': output.relative_to(root).as_posix(),
                  'semantic_cache_metadata_sha256': sha256_file(root / cfg['cache'] / 'metadata.json'),
                  'cache_identity': metadata['identity'], 'seed': train_cfg['seed'], 'packages': versions,
                  'training_config': train_cfg, 'train_rows': len(train_y),
                  'full_train_rows': full_train_rows,
                  'data_regime': 'FULL' if len(train_y) == full_train_rows else 'SUBSAMPLED',
                  'train_indices': chosen.tolist(),
                  'label_provenance': 'rating-derived proxy', 'selection_metric': 'macro_f1',
                  'test_exposure': 'Split test đã được đánh giá trong LEGACY; không tune benchmark mới bằng test',
                  'cuda': torch.version.cuda, 'gpu': torch.cuda.get_device_name(0)}
    write_json(report_dir / 'config.json', provenance)
    start = time.perf_counter()
    candidates, best, best_model, best_spec = [], -1., None, None
    def predict(model, matrix):
        if experiment == 'E00_majority':
            return np.full(len(matrix), int(model), dtype='int64')
        if experiment == 'E02_tabm_embedding':
            return tabm_predict(model, matrix, device=train_cfg['device'], batch_size=train_cfg['tabm']['batch_size'])
        if experiment in VERSIONS:
            batch = train_cfg['tabpfn']['prediction_batch_size']
            predictions = []
            for i in range(0, len(matrix), batch):
                predictions.append(model.predict(np.array(matrix[i:i+batch])))
                print(f'{experiment} predict={min(i+batch, len(matrix))}/{len(matrix)}', flush=True)
                if time.perf_counter() - start > train_cfg['max_seconds_per_experiment']:
                    raise RuntimeError('Vượt trần thời gian experiment')
            return np.concatenate(predictions)
        return model.predict(matrix)
    try:
        with ResourceMonitor() as monitor:
            if experiment == 'E00_majority':
                specs = [{'weighted': False}]
            elif experiment == 'E01_xgboost_embedding':
                specs = [{**params, 'weighted': weighted} for params in train_cfg['xgboost'] for weighted in [False, True]]
            elif experiment == 'E02_tabm_embedding':
                specs = [{'weighted': weighted} for weighted in [False, True]]
            else:
                specs = [{'weighted': False, 'version': VERSIONS[experiment]}]
            for index, spec in enumerate(specs):
                seed_everything(train_cfg['seed'])
                before = time.perf_counter()
                history = []
                if experiment == 'E00_majority':
                    model = int(np.bincount(train_y, minlength=3).argmax())
                elif experiment == 'E01_xgboost_embedding':
                    from xgboost import XGBClassifier
                    params = {k: v for k, v in spec.items() if k != 'weighted'}
                    model = XGBClassifier(**params, objective='multi:softprob', num_class=3,
                        tree_method='hist', device='cpu', n_jobs=train_cfg['threads'], random_state=train_cfg['seed'])
                    # Smoke nhỏ trên train trước fit full. Không dùng score smoke để chọn tham số.
                    smoke_ids = np.concatenate([np.flatnonzero(train_y == i)[:8] for i in range(3)])
                    smoke = XGBClassifier(n_estimators=2, max_depth=2, n_jobs=2, objective='multi:softprob', num_class=3)
                    smoke.fit(train_x[smoke_ids], train_y[smoke_ids])
                    smoke.predict(train_x[smoke_ids[:3]])
                    weights = balanced_weights(train_y)[train_y] if spec['weighted'] else None
                    model.fit(train_x, train_y, sample_weight=weights)
                elif experiment == 'E02_tabm_embedding':
                    model, history = train_tabm(train_x, train_y, val_x, val_y,
                        config=train_cfg['tabm'], device=train_cfg['device'], weighted=spec['weighted'],
                        max_seconds=train_cfg['max_seconds_per_experiment'] - (time.perf_counter()-start),
                        memory_limit=train_cfg['max_process_rss_bytes'])
                else:
                    # Attempt thật trên train nhỏ; gating/license/OOM được ghi nguyên trạng.
                    settings = {k: v for k, v in train_cfg['tabpfn'].items() if k != 'prediction_batch_size'}
                    model = make_tabpfn(experiment, **settings, device=train_cfg['device'], random_state=train_cfg['seed'])
                    smoke_ids = np.concatenate([np.flatnonzero(train_y == i)[:8] for i in range(3)])
                    model.fit(np.array(train_x[smoke_ids]), train_y[smoke_ids])
                    model.predict(np.array(train_x[smoke_ids[:3]]))
                    write_json(report_dir / 'smoke.json', {'status': 'PASS', 'rows': len(smoke_ids),
                        'checkpoint': Path(model.model_path).name, 'gpu_allocated_bytes': torch.cuda.max_memory_allocated()})
                    del model
                    gc.collect()
                    torch.cuda.empty_cache()
                    model = make_tabpfn(experiment, **settings, device=train_cfg['device'], random_state=train_cfg['seed'])
                    model.fit(np.array(train_x), train_y)
                prediction = predict(model, val_x)
                val_metrics = metrics(val_y, prediction)
                entry = {'candidate': index, 'spec': spec, 'fit_validation_seconds': time.perf_counter()-before,
                         'validation_metrics': val_metrics, 'history': history}
                candidates.append(entry)
                write_json(report_dir / 'candidates.json', {'candidates': candidates})
                print(f'{experiment} candidate={index} macro_f1={val_metrics["macro_f1"]:.6f}', flush=True)
                if val_metrics['macro_f1'] > best + 1e-12:
                    best, best_model, best_spec = val_metrics['macro_f1'], model, spec
                    if experiment == 'E01_xgboost_embedding':
                        model.save_model(output / 'model.ubj')
                    elif experiment == 'E02_tabm_embedding':
                        torch.save({k: v.cpu().clone() for k, v in model.state_dict().items()}, output / 'model.pt')
                    elif experiment in VERSIONS:
                        joblib.dump(model, output / 'model.joblib')
                    else:
                        write_json(output / 'model.json', {'majority_id': model})
                    np.save(report_dir / 'validation_predictions.npy', prediction, allow_pickle=False)
                if time.perf_counter() - start > train_cfg['max_seconds_per_experiment']:
                    raise RuntimeError('Vượt trần thời gian experiment; không mở test')
                if monitor.peak_rss_bytes > train_cfg['max_process_rss_bytes']:
                    raise RuntimeError('Vượt trần RSS trước selection/test; giữ bằng chứng để retry mẫu nhỏ hơn')
            lock = {**provenance, 'selected_spec': best_spec, 'validation_macro_f1': best,
                    'selection_complete_before_test': True, 'selection_seconds': time.perf_counter()-start,
                    'model_sha256': {p.name: sha256_file(p) for p in output.iterdir()}}
            write_json(report_dir / 'selection_lock.json', lock)
            # Load artifact đã khóa để kiểm tra reload trước lần đánh giá test.
            if experiment == 'E01_xgboost_embedding':
                from xgboost import XGBClassifier
                best_model = XGBClassifier()
                best_model.load_model(output / 'model.ubj')
            elif experiment == 'E02_tabm_embedding':
                from src.sentiment.modern import make_tabm
                best_model = make_tabm(train_x.shape[1], train_cfg['tabm'], train_cfg['device'])
                best_model.load_state_dict(torch.load(output / 'model.pt', map_location=train_cfg['device'], weights_only=True))
            elif experiment in VERSIONS:
                del model, best_model
                gc.collect()
                torch.cuda.empty_cache()
                best_model = joblib.load(output / 'model.joblib')
            val_prediction = predict(best_model, val_x)
            if not np.array_equal(val_prediction, np.load(report_dir / 'validation_predictions.npy')):
                raise ValueError('Reload validation predictions không khớp')
            test_x = np.load(root / cfg['cache'] / 'test_embeddings.npy', mmap_mode='r')
            before = time.perf_counter()
            test_prediction = predict(best_model, test_x)
            prediction_seconds = time.perf_counter() - before
            test_metrics = metrics(test_frame.label_id.to_numpy(), test_prediction)
            np.save(report_dir / 'test_predictions.npy', test_prediction, allow_pickle=False)
            test_frame[['review_id', 'label_id']].assign(prediction_id=test_prediction).to_parquet(report_dir / 'test_predictions.parquet', index=False)
            data['validation']['frame'][['review_id', 'label_id']].assign(prediction_id=val_prediction).to_parquet(report_dir / 'validation_predictions.parquet', index=False)
            write_json(report_dir / 'test_metrics.json', test_metrics)
            write_json(report_dir / 'validation_metrics.json', metrics(val_y, val_prediction))
            pd.DataFrame(test_metrics['confusion_matrix'], index=['negative', 'neutral', 'positive'],
                columns=['negative', 'neutral', 'positive']).to_csv(report_dir / 'confusion_matrix.csv')
        result = {**provenance, 'status': 'PASS', 'selected_spec': best_spec, 'test_metrics': test_metrics,
                  'validation_macro_f1': best, 'selection_seconds': lock['selection_seconds'],
                  'runtime_seconds': monitor.seconds, 'test_prediction_seconds': prediction_seconds,
                  'inference_ms_per_review': prediction_seconds / len(test_frame) * 1000,
                  'peak_process_rss_bytes': monitor.peak_rss_bytes,
                  'peak_gpu_allocated_bytes': torch.cuda.max_memory_allocated(),
                  'peak_gpu_reserved_bytes': torch.cuda.max_memory_reserved(),
                  'artifact_bytes': sum(p.stat().st_size for p in output.iterdir())}
        write_json(report_dir / 'result.json', result)
        if attempt is not None:
            write_json(base_report / 'latest_attempt.json', {'attempt': attempt})
        write_json(output / 'metadata.json', {**lock, 'representation': 'majority sanity' if experiment == 'E00_majority' else 'frozen semantic embedding'})
        pd.DataFrame([{**flat_metrics(test_metrics), 'balanced_accuracy': test_metrics['balanced_accuracy']}]).to_csv(report_dir / 'metrics.csv', index=False)
        return result
    except Exception as exc:
        status = 'BLOCKED' if experiment in VERSIONS and ('license' in str(exc).lower() or 'gated' in str(exc).lower() or 'token' in str(exc).lower()) else 'FAILED'
        from src.evaluation.redaction import safe_error
        result = {**provenance, 'status': status, 'error_type': type(exc).__name__, 'error': safe_error(exc),
                  'elapsed_seconds': time.perf_counter()-start,
                  'peak_gpu_allocated_bytes': torch.cuda.max_memory_allocated(),
                  'NEXT_ACTION': 'Cấp quyền checkpoint hợp lệ rồi chạy experiment ở suffix mới; không dùng default khác hoặc tune test'}
        write_json(report_dir / 'result.json', result)
        if attempt is not None:
            write_json(base_report / 'latest_attempt.json', {'attempt': attempt})
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('experiment', choices=ORDER)
    parser.add_argument('--attempt', help='Tên lần thử mới; chỉ retry lỗi trước selection/test, giữ bằng chứng cũ')
    parser.add_argument('--train-samples', type=int, help='Chỉ TabPFN: subsample phân tầng seed42 sau đo tài nguyên')
    args = parser.parse_args()
    try:
        result = run(args.experiment, attempt=args.attempt, train_samples=args.train_samples)
    except Exception as exc:
        print(json.dumps({'status': 'FAILED', 'error_type': type(exc).__name__}))
        raise SystemExit(1) from None
    print(json.dumps({'experiment': args.experiment, 'status': result['status']}))


if __name__ == '__main__':
    main()
