"""Đo tài nguyên TabPFN tăng dần bằng train-only, cô lập từng phép đo."""

import argparse
import contextlib
import importlib.metadata
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import time

os.environ.setdefault('TABPFN_NO_BROWSER', '1')
os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG', ':4096:8')


def stratified_ids(labels, size, seed=42):
    """Lấy mẫu xác định, giữ tỷ lệ lớp; trả chỉ số theo thứ tự nguồn."""
    import numpy as np
    from sklearn.model_selection import train_test_split
    if size == len(labels):
        return np.arange(len(labels))
    chosen, _ = train_test_split(np.arange(len(labels)), train_size=size,
                                stratify=labels, random_state=seed)
    return np.sort(chosen)


def worker(version, size, device, batch, output, fit_mode='low_memory'):
    result = {'version': version, 'samples': size, 'device': device,
              'prediction_batch_size': batch, 'split': 'train', 'seed': 42,
              'status': 'ERROR', 'token_configured': bool(os.environ.get('TABPFN_TOKEN', '').strip())}
    start = time.perf_counter()
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        try:
            import numpy as np
            import torch
            import yaml
            from src.config import PROJECT_ROOT
            from src.evaluation.classification import ResourceMonitor
            from src.sentiment.tabpfn_versions import make_tabpfn
            cfg = yaml.safe_load((PROJECT_ROOT / 'configs/modern_tabular.yaml').read_text(encoding='utf-8'))
            cache = PROJECT_ROOT / 'data/processed/features/semantic_20261024'
            x = np.load(cache / 'train_embeddings.npy', mmap_mode='r')
            y = np.load(cache / 'train_labels.npy')
            ids = stratified_ids(y, size)
            probes = np.setdiff1d(np.arange(len(y)), ids)[:batch]
            if len(probes) < batch:
                probes = np.arange(batch)
            settings = {k: v for k, v in cfg['tabpfn'].items() if k != 'prediction_batch_size'}
            settings['fit_mode'] = fit_mode
            if device == 'cpu':
                settings['inference_precision'] = 'auto'
            torch.set_num_threads(2)
            if device == 'cuda':
                torch.cuda.reset_peak_memory_stats()
            experiment = 'E03_tabpfn_v3_embedding' if version == 'V3' else 'E04_tabpfn_v35_embedding'
            result.update(features=int(x.shape[1]), dtype=str(x.dtype), settings=settings,
                          package=importlib.metadata.version('tabpfn'),
                          class_counts=np.bincount(y[ids], minlength=3).tolist())
            assert result['package'] == '9.2.0'
            with ResourceMonitor() as monitor:
                model = make_tabpfn(experiment, **settings, device=device, random_state=42)
                result['checkpoint'] = Path(model.model_path).name
                before = time.perf_counter()
                model.fit(np.array(x[ids]), y[ids])
                if device == 'cuda':
                    torch.cuda.synchronize()
                result['fit_seconds'] = time.perf_counter() - before
                before = time.perf_counter()
                prediction = model.predict(np.array(x[probes]))
                if device == 'cuda':
                    torch.cuda.synchronize()
                result['inference_seconds'] = time.perf_counter() - before
                before = time.perf_counter()
                model.predict(np.array(x[probes]))
                if device == 'cuda':
                    torch.cuda.synchronize()
                result['warm_inference_seconds'] = time.perf_counter() - before
                result.update(probe_rows=len(probes), status='PASS')
                assert len(prediction) == len(probes)
            result['peak_process_rss_bytes'] = monitor.peak_rss_bytes
            result['peak_gpu_allocated_bytes'] = torch.cuda.max_memory_allocated() if device == 'cuda' else 0
            result['peak_gpu_reserved_bytes'] = torch.cuda.max_memory_reserved() if device == 'cuda' else 0
        except Exception as exc:
            result['error_type'] = type(exc).__name__
            result['status'] = 'OOM' if 'outofmemory' in type(exc).__name__.lower() else 'ERROR'
            from src.evaluation.redaction import safe_error
            result['error'] = safe_error(exc)
    result['seconds'] = time.perf_counter() - start
    Path(output).write_text(json.dumps(result, indent=2), encoding='utf-8')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('version', choices=['V3', 'V3_5'])
    p.add_argument('--size', type=int)
    p.add_argument('--device', default='cuda')
    p.add_argument('--batch', type=int, default=16)
    p.add_argument('--output')
    p.add_argument('--fit-mode', default='low_memory')
    args = p.parse_args()
    if args.size:
        worker(args.version, args.size, args.device, args.batch, args.output, args.fit_mode)
        return
    root = Path(__file__).resolve().parents[1]
    out = root / 'reports' / 'tabpfn_resources_20261024' / args.version
    out.mkdir(parents=True, exist_ok=True)
    for size in [500, 1000, 2500, 5000, 10000, 21000]:
        path = out / f'{size}_cuda_b16.json'
        if not path.exists():
            try:
                subprocess.run([sys.executable, '-m', 'scripts.assess_tabpfn', args.version,
                                '--size', str(size), '--output', str(path)],
                               cwd=root, timeout=180, capture_output=True, check=False)
            except subprocess.TimeoutExpired:
                path.write_text(json.dumps({'status': 'TIMEOUT', 'samples': size,
                    'version': args.version, 'timeout_seconds': 180, 'split': 'train'}), encoding='utf-8')
        row = json.loads(path.read_text(encoding='utf-8'))
        print(json.dumps(row), flush=True)
        if row['status'] != 'PASS':
            break
        if row.get('peak_process_rss_bytes', 0) > 6000000000:
            print('LIMITED: RSS vượt6GB; dừng tăng mẫu, chuyển cấu hình memory-safe.', flush=True)
            break


if __name__ == '__main__':
    main()
