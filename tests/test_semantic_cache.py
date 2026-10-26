"""Cache fixture nhỏ kiểm tra hash, alignment và invalidation thực sự."""

import json

import numpy as np
import pandas as pd
import pytest

from src.data.acquisition import sha256_file
from src.preprocessing.semantic import canonical_text, embedding_columns, ordered_digest
from src.preprocessing.semantic_cache import cache_identity, load_cache


@pytest.fixture
def cache_fixture(tmp_path):
    cfg = {'source': 'source.parquet', 'splits': 'splits', 'cache': 'cache',
           'encoder': {'dimension': 3}, 'transformer': {'tokenizer': 'tokenizer.json'}}
    (tmp_path / 'splits').mkdir()
    (tmp_path / 'cache').mkdir()
    (tmp_path / 'tokenizer.json').write_text('{}', encoding='utf-8')
    frames = []
    for s in ['train', 'validation', 'test']:
        f = pd.DataFrame({'review_id': [s+'0', s+'1'], 'review_title': ['Title', None],
                          'text': ['not good!', 'okay'], 'label_id': [0, 1]})
        frames.append(f)
        f.to_parquet(tmp_path / 'splits' / f'{s}.parquet', index=False)
        pd.DataFrame({'review_id': f.review_id, 'row_index': [0, 1],
                      'text_sha256': [ordered_digest([t]) for t in canonical_text(f)]}).to_parquet(
                          tmp_path / 'cache' / f'{s}_mapping.parquet', index=False)
        np.save(tmp_path / 'cache' / f'{s}_labels.npy', np.array([0, 1]))
        np.save(tmp_path / 'cache' / f'{s}_embeddings.npy', np.ones((2, 3), dtype='float32'))
    pd.concat(frames).to_parquet(tmp_path / 'source.parquet', index=False)
    meta = {'status': 'PASS', 'identity': cache_identity(cfg, tmp_path),
            'feature_columns': embedding_columns(3),
            'files_sha256': {p.name: sha256_file(p) for p in (tmp_path / 'cache').iterdir()}}
    (tmp_path / 'cache/metadata.json').write_text(json.dumps(meta), encoding='utf-8')
    return tmp_path, cfg


def test_cache_valid_and_config_invalidation(cache_fixture):
    root, cfg = cache_fixture
    data, _ = load_cache(cfg, root)
    assert data['train']['X'].shape == (2, 3)
    with pytest.raises(ValueError, match='hết hiệu lực'):
        load_cache({**cfg, 'seed': 43}, root)


def test_cache_corruption(cache_fixture):
    root, cfg = cache_fixture
    np.save(root / 'cache/train_labels.npy', np.array([1, 0]))
    with pytest.raises(ValueError, match='Cache hỏng'):
        load_cache(cfg, root)


def test_alignment_even_after_rehash(cache_fixture):
    root, cfg = cache_fixture
    path = root / 'cache/train_mapping.parquet'
    f = pd.read_parquet(path).iloc[::-1]
    f.to_parquet(path, index=False)
    meta_path = root / 'cache/metadata.json'
    meta = json.loads(meta_path.read_text(encoding='utf-8'))
    meta['files_sha256'][path.name] = sha256_file(path)
    meta_path.write_text(json.dumps(meta), encoding='utf-8')
    with pytest.raises(ValueError, match='alignment'):
        load_cache(cfg, root)
