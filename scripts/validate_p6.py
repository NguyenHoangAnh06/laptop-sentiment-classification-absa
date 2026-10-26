"""Kiểm tra P6 chỉ đọc mà không cần lắp hoặc chạy lại kiểm thử suy luận."""

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import PROJECT_ROOT
from src.data.acquisition import sha256_file
from src.evaluation.classification import classification_metrics, flat_metrics
from src.models.registry import load_sentiment


def validate(report: Path, root: Path = PROJECT_ROOT) -> dict:
    """Kiểm tra giá trị băm, lựa chọn chỉ tập xác thực, dự đoán đã lưu và tải lại hợp đồng."""
    report = Path(report)
    manifest = json.loads((report / 'manifest.json').read_text(encoding='utf-8'))
    for group in ('input_sha256', 'output_sha256', 'implementation_sha256'):
        for rel, digest in manifest[group].items():
            if sha256_file(root / rel) != digest:
                raise ValueError(f'Changed artifact: {rel}')
    lock_path = report / 'selection_lock.json'
    if sha256_file(lock_path) != manifest['selection_lock_sha256']:
        raise ValueError('Changed selection lock')
    lock = json.loads(lock_path.read_text(encoding='utf-8'))
    history = json.loads((report / 'training_history.json').read_text(encoding='utf-8'))
    cfg = json.loads((report / 'config.json').read_text(encoding='utf-8'))
    p4 = json.loads((root / cfg['p4_manifest']).read_text(encoding='utf-8'))
    train = pd.read_parquet(root / p4['paths']['splits'] / 'train.parquet', columns=['review_id', 'label_id'])
    for choice in lock['candidate_choices']:
        rows = [row for row in history if row['mode'] == choice['mode']]
        best = max(rows, key=lambda row: row['validation']['macro_f1'])
        if best['validation'] != choice['validation'] or best['epoch'] != choice['best_epoch']:
            raise ValueError('Candidate checkpoint not chosen by validation macro F1')
        if any(row['train_rows'] != len(train) for row in rows):
            raise ValueError('Incomplete train epoch')
        expected = (len(train) / (3 * np.bincount(train.label_id, minlength=3))).tolist()
        if choice['mode'] == 'balanced' and not np.allclose(rows[0]['class_weights'], expected):
            raise ValueError('Class weights differ from training frequencies')
    if lock['selected'] != max(lock['candidate_choices'], key=lambda c: c['validation']['macro_f1']):
        raise ValueError('Overall BERT selection not validation-only')
    models = root / 'artifacts/models' / cfg['output_suffix']
    scores = json.loads((report / 'metrics.json').read_text(encoding='utf-8'))
    benchmark = pd.read_csv(report / 'benchmark.csv').set_index('model')
    for split in ('validation', 'test'):
        predictions = pd.read_parquet(models / f'{split}_predictions.parquet')
        targets = pd.read_parquet(root / p4['paths']['splits'] / f'{split}.parquet', columns=['review_id', 'label_id'])
        pd.testing.assert_frame_equal(predictions[['review_id', 'label_id']], targets)
        metrics = classification_metrics(predictions.label_id, predictions.prediction_id)
        for key in ('accuracy', 'macro_f1', 'weighted_f1', 'per_class', 'confusion_matrix'):
            if metrics[key] != scores[split][key]:
                raise ValueError(f'{split} metrics differ from saved predictions')
        cm = pd.read_csv(report / f'{split}_confusion_matrix.csv', index_col=0)
        np.testing.assert_array_equal(cm.to_numpy(), metrics['confusion_matrix'])
        if split == 'test':
            for key, value in flat_metrics(metrics).items():
                if not np.isclose(benchmark.loc['bert', key], value, rtol=1e-12, atol=1e-12):
                    raise ValueError('Benchmark differs from saved metrics')
    selected_dir = models / lock['selected']['mode']
    if sha256_file(selected_dir / 'model.safetensors') != lock['checkpoint_sha256']:
        raise ValueError('Test checkpoint differs from selection lock')
    # Bằng chứng phụ thuộc vào bộ đệm tùy chọn cho thấy trọng số đã huấn luyện trước mạng nền thực đã thay đổi.
    # tệp kết quả được xuất di động không yêu cầu giữ lại bộ đệm HF.
    from huggingface_hub import try_to_load_from_cache
    from safetensors import safe_open
    import torch
    source = json.loads((report / 'pretrained_source.json').read_text(encoding='utf-8'))
    cached = try_to_load_from_cache(cfg['checkpoint'], 'model.safetensors', revision=cfg['revision'])
    backbone_check = 'NOT_CHECKED: matching pretrained cache unavailable'
    if isinstance(cached, str) and sha256_file(Path(cached)) == source['sha256']:
        with safe_open(cached, framework='pt', device='cpu') as initial, safe_open(
                selected_dir / 'model.safetensors', framework='pt', device='cpu') as tuned:
            for key in ('bert.embeddings.word_embeddings.weight', 'bert.encoder.layer.0.attention.self.query.weight'):
                if torch.equal(initial.get_tensor(key), tuned.get_tensor(key)):
                    raise ValueError('Selected backbone parameter unchanged from pretrained source')
        backbone_check = 'PASS: embeddings and encoder query weights differ from pinned pretrained source'
    artifact = load_sentiment(selected_dir, family='bert', device='cpu')
    frame = pd.read_parquet(root / p4['paths']['splits'] / 'validation.parquet').iloc[:4]
    one, two = artifact.predict(frame), artifact.predict(frame)
    if one != two or any(p['aspects'] or p['confidence'] is not None for p in one):
        raise ValueError('Invalid or nondeterministic exported inference')
    return {'status': 'PASS', 'input_hashes_verified': len(manifest['input_sha256']),
            'saved_prediction_metrics': 'PASS', 'validation_selection': 'PASS',
            'full_train_epochs': 'PASS', 'cpu_reload_inference': 'PASS',
            'backbone_update': backbone_check,
            'test_predictions_rerun': False, 'P7_executed': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', type=Path, default=PROJECT_ROOT / 'reports/p6/p6_20261015')
    args = parser.parse_args()
    print(json.dumps(validate(args.report), indent=2))


if __name__ == '__main__':
    main()
