"""Smoke riêng từng phiên bản TabPFN trên tập train nhỏ, không chạy benchmark."""

import argparse
import contextlib
import importlib.metadata
import io
import json
import os
import time
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('version', choices=['V3', 'V3_5'])
    args = parser.parse_args()
    os.environ.setdefault('TABPFN_NO_BROWSER', '1')
    os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG', ':4096:8')
    root = Path(__file__).resolve().parents[1]
    output = root / 'reports' / 'tabpfn_smoke_20261024' / f'{args.version}.json'
    if output.exists():
        raise FileExistsError('Không ghi đè báo cáo smoke đã có')
    result = {'version': args.version, 'token_configured': bool(os.environ.get('TABPFN_TOKEN', '').strip()),
              'status': 'BLOCKED', 'full_dataset_run': False, 'split': 'train',
              'purpose': 'Kiểm tra kỹ thuật; không phải đánh giá chất lượng mô hình'}
    started = time.perf_counter()
    # Không xuất log thư viện/exception có thể chứa thông tin xác thực.
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        try:
            if not result['token_configured']:
                raise RuntimeError('Thiếu TABPFN_TOKEN')
            import numpy as np
            import torch
            import yaml
            from src.sentiment.tabpfn_versions import make_tabpfn

            result['tabpfn_package'] = importlib.metadata.version('tabpfn')
            if result['tabpfn_package'] != '9.2.0':
                raise RuntimeError('Cần package tabpfn==9.2.0')
            config = yaml.safe_load((root / 'configs/modern_tabular.yaml').read_text(encoding='utf-8'))
            cache = root / 'data/processed/features/semantic_20261024'
            x = np.load(cache / 'train_embeddings.npy', mmap_mode='r')
            y = np.load(cache / 'train_labels.npy', mmap_mode='r')
            ids = np.concatenate([np.flatnonzero(y == label)[:9] for label in range(3)])
            if len(ids) != 27:
                raise ValueError('Không đủ mẫu cho smoke ba lớp')
            ids = ids.reshape(3, 9)
            fit_ids, predict_ids = ids[:, :8].ravel(), ids[:, 8].ravel()
            result.update(fit_rows=24, predict_rows=3, features=int(x.shape[1]),
                          fit_indices=fit_ids.tolist(), predict_indices=predict_ids.tolist())
            settings = {k: v for k, v in config['tabpfn'].items() if k != 'prediction_batch_size'}
            torch.set_num_threads(config['threads'])
            torch.cuda.reset_peak_memory_stats()
            experiment = 'E03_tabpfn_v3_embedding' if args.version == 'V3' else 'E04_tabpfn_v35_embedding'
            model = make_tabpfn(experiment, **settings, device=config['device'], random_state=42)
            result['checkpoint'] = Path(model.model_path).name
            result['settings'] = settings
            model.fit(np.array(x[fit_ids]), np.array(y[fit_ids]))
            prediction = model.predict(np.array(x[predict_ids]))
            if prediction.shape != (3,) or not set(prediction.tolist()) <= {0, 1, 2}:
                raise ValueError('Đầu ra dự đoán không hợp lệ')
            result.update(status='PASS', prediction_ids=prediction.tolist(),
                          peak_gpu_allocated_bytes=torch.cuda.max_memory_allocated())
        except Exception as exc:
            result['error_type'] = type(exc).__name__
            result['error_detail'] = 'Không lưu thông báo lỗi nhằm bảo vệ token; kiểm tra quyền license/checkpoint nếu lỗi truy cập.'
    result['elapsed_seconds'] = time.perf_counter() - started
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=True))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
