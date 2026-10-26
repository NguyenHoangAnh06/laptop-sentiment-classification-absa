"""Kiểm tra cache semantic với hash nguồn, cấu hình và alignment từng split."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from src.config import PROJECT_ROOT
from src.data.acquisition import sha256_file
from src.preprocessing.semantic import canonical_text, ordered_digest, validate_matrix

SPLITS = ('train', 'validation', 'test')


def load_semantic_config(root: Path = PROJECT_ROOT) -> dict:
    cfg = yaml.safe_load((root / 'configs/semantic_benchmark.yaml').read_text(encoding='utf-8'))
    if cfg['canonical_text'] != {'title_field': 'review_title', 'body_field': 'text',
                                  'separator': '\n', 'normalization': 'nfc_whitespace_v1'}:
        raise ValueError('Chính sách canonical text chưa được triển khai')
    return cfg


def cache_identity(cfg: dict, root: Path = PROJECT_ROOT) -> dict:
    """Mọi thay đổi dữ liệu/split/encoder/text policy làm mất hiệu lực cache."""
    return {'dataset_hash': sha256_file(root / cfg['source']),
            'split_hash': {s: sha256_file(root / cfg['splits'] / f'{s}.parquet') for s in SPLITS},
            'configuration_hash': ordered_digest([cfg]),
            'tokenizer_hash': sha256_file(root / cfg['transformer']['tokenizer'])}


def load_cache(cfg: dict, root: Path = PROJECT_ROOT) -> tuple[dict, dict]:
    cache = root / cfg['cache']
    metadata = json.loads((cache / 'metadata.json').read_text(encoding='utf-8'))
    if metadata['status'] != 'PASS' or metadata['identity'] != cache_identity(cfg, root):
        raise ValueError('Cache hết hiệu lực hoặc chưa hoàn chỉnh')
    for name, digest in metadata['files_sha256'].items():
        if sha256_file(cache / name) != digest:
            raise ValueError(f'Cache hỏng: {name}')
    data = {}
    for split in SPLITS:
        frame = pd.read_parquet(root / cfg['splits'] / f'{split}.parquet')
        mapping = pd.read_parquet(cache / f'{split}_mapping.parquet')
        labels = np.load(cache / f'{split}_labels.npy', allow_pickle=False)
        matrix = np.load(cache / f'{split}_embeddings.npy', allow_pickle=False, mmap_mode='r')
        if (mapping.review_id.tolist() != frame.review_id.tolist()
                or mapping.row_index.tolist() != list(range(len(frame)))
                or labels.tolist() != frame.label_id.tolist()
                or mapping.text_sha256.tolist() != [ordered_digest([t]) for t in canonical_text(frame)]):
            raise ValueError(f'Sai alignment ID/text/label: {split}')
        validate_matrix(matrix, rows=len(frame), dimension=cfg['encoder']['dimension'],
                        feature_columns=metadata['feature_columns'])
        data[split] = {'X': matrix, 'y': labels, 'frame': frame}
    return data, metadata
