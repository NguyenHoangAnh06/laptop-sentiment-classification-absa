"""P4: giữ split, encode frozen một lần, QA và cache riêng nhánh token BERT."""

import json
import os
import time
from datetime import datetime, timezone
from itertools import combinations

os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')
os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG', ':4096:8')

import numpy as np
import pandas as pd
import torch
from sentence_transformers import SentenceTransformer
from tokenizers import Tokenizer

from scripts.revalidate_model_data import write_json
from src.config import PROJECT_ROOT
from src.data.acquisition import sha256_file
from src.data.near_duplicates import audit_near_duplicates
from src.evaluation.classification import ResourceMonitor
from src.preprocessing.semantic import (TEXT_DEFINITION, canonical_text, embedding_columns,
                                        ordered_digest, validate_matrix)
from src.preprocessing.semantic_cache import SPLITS, cache_identity, load_cache, load_semantic_config


def validate_reused_splits(frames: dict, source: pd.DataFrame) -> dict:
    """Không phân chia lại; so khớp mọi ô và kiểm tra overlap trên các khóa hiện có."""
    expected = {'train': (21000, 6357, [5781, 1842, 13377]),
                'validation': (4500, 1361, [1239, 395, 2866]),
                'test': (4500, 1362, [1239, 394, 2867])}
    source_sorted = source.sort_values('review_id').reset_index(drop=True)
    joined = pd.concat(list(frames.values()), ignore_index=True)
    pd.testing.assert_frame_equal(source_sorted,
        joined[source.columns].sort_values('review_id').reset_index(drop=True))
    counts, overlaps = {}, {}
    for split, frame in frames.items():
        rows, products, labels = expected[split]
        if (len(frame) != rows or frame.parent_asin.nunique() != products
                or np.bincount(frame.label_id, minlength=3).tolist() != labels
                or not frame.split.eq(split).all() or frame.review_id.duplicated().any()):
            raise ValueError(f'Sai số liệu split: {split}')
        counts[split] = {'rows': rows, 'products': products, 'classes': labels}
    for a, b in combinations(SPLITS, 2):
        overlap = {}
        for column in ['review_id', 'parent_asin', 'asin', 'split_group_id', 'clean_text_sha256', 'text', 'near_duplicate_group_id']:
            if column in frames[a]:
                overlap[column] = len(set(frames[a][column].dropna()) & set(frames[b][column].dropna()))
        overlap['canonical_text'] = len(set(canonical_text(frames[a])) & set(canonical_text(frames[b])))
        if any(overlap.values()):
            raise ValueError(f'Có overlap {a}/{b}: {overlap}')
        overlaps[f'{a}__{b}'] = overlap
    rows = [{'review_id': row.review_id, 'text': text, 'sentiment': row.sentiment}
            for frame in frames.values() for row, text in zip(frame.itertuples(), canonical_text(frame))]
    pairs, audit = audit_near_duplicates(rows, seed=42)
    by_id = {v: s for s, f in frames.items() for v in f.review_id}
    cross = [p for p in pairs if by_id[p['review_id_a']] != by_id[p['review_id_b']]]
    if cross or audit['comparison_cap_reached']:
        raise ValueError('Canonical near-duplicate cross-split hoặc audit chưa hoàn tất')
    return {'status': 'PASS', 'counts': counts, 'overlaps': overlaps, 'near_audit': audit,
            'cross_split_near_pairs': len(cross), 'resplit': False,
            'limits': 'Kiểm tra gần trùng từ vựng xấp xỉ; không chứng minh cách ly mọi paraphrase'}


def main() -> None:
    root = PROJECT_ROOT
    cfg = load_semantic_config(root)
    if json.loads((root / 'reports/p3_model_readiness.json').read_text(encoding='utf-8'))['status'] != 'PASS':
        raise ValueError('P3 chưa PASS')
    cache = root / cfg['cache']
    if cache.exists():
        load_cache(cfg, root)
        print('PASS: cache hiện có được xác minh; không encode lại')
        return
    frames = {s: pd.read_parquet(root / cfg['splits'] / f'{s}.parquet') for s in SPLITS}
    isolation = validate_reused_splits(frames, pd.read_parquet(root / cfg['source']))
    write_json(root / 'reports/p4_semantic_split_validation.json', isolation)
    identity = cache_identity(cfg, root)
    seed = cfg['seed']
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.set_num_threads(2)
    torch.use_deterministic_algorithms(True)
    enc = cfg['encoder']
    if enc['device'] == 'cuda' and not torch.cuda.is_available():
        raise ValueError('CUDA cấu hình không có; không âm thầm đổi thiết bị')
    model = SentenceTransformer(enc['model'], revision=enc['revision'], device=enc['device'],
                                trust_remote_code=False)
    model.max_seq_length = enc['max_length']
    model.eval()
    model.requires_grad_(False)
    if model.get_embedding_dimension() != enc['dimension']:
        raise ValueError('Sai dimension encoder')
    pooling = model[1]
    if pooling.pooling_mode != 'mean':
        raise ValueError('Pooling model không khớp mean pooling được ghi nhận')
    texts = canonical_text(frames['train'].iloc[:128])
    def encode(values):
        with torch.inference_mode():
            return model.encode(values, batch_size=enc['batch_size'],
                normalize_embeddings=enc['normalize_embeddings'], convert_to_numpy=True,
                show_progress_bar=False).astype(np.float32)
    encode(texts[:8])
    torch.cuda.reset_peak_memory_stats()
    with ResourceMonitor() as monitor:
        before = time.perf_counter()
        sample = encode(texts)
        torch.cuda.synchronize()
        elapsed = time.perf_counter() - before
    replay = encode(texts)
    deterministic = bool(np.allclose(sample, replay, atol=1e-6, rtol=1e-5))
    duplicate = encode([texts[0], texts[0]])
    if not deterministic or not np.allclose(duplicate[0], duplicate[1], atol=1e-6):
        raise ValueError('Encoder sample không tái lập')
    benchmark = {'rows': len(texts), 'seconds': elapsed, 'reviews_per_second': len(texts) / elapsed,
                 'peak_process_rss_bytes': monitor.peak_rss_bytes,
                 'peak_gpu_allocated_bytes': torch.cuda.max_memory_allocated(),
                 'peak_gpu_reserved_bytes': torch.cuda.max_memory_reserved(),
                 'deterministic_sample': deterministic, 'duplicate_consistency': True,
                 'selected_encoder': enc,
                 'reason': 'MiniLM 6 lớp, 384 chiều và sample đo trực tiếp phù hợp VRAM 6GB; không chọn dựa trên nhãn hoặc test score',
                 'limits': 'Một encoder được đo; không khẳng định tối ưu hơn các encoder chưa thử; max_length256 có truncation'}
    write_json(root / 'reports/p4_encoder_benchmark.json', benchmark)
    cache.mkdir(parents=True, exist_ok=False)
    tokenizer = Tokenizer.from_file(str(root / cfg['transformer']['tokenizer']))
    tokenizer.no_padding()
    tokenizer.enable_truncation(max_length=cfg['transformer']['max_length'])
    qa = {}
    for split, frame in frames.items():
        texts = canonical_text(frame)
        torch.cuda.reset_peak_memory_stats()
        with ResourceMonitor() as monitor:
            matrix = encode(texts)
        qa[split] = validate_matrix(matrix, rows=len(frame), dimension=enc['dimension'],
                                     feature_columns=embedding_columns(enc['dimension']))
        if not np.allclose(np.linalg.norm(matrix, axis=1), 1., atol=1e-4):
            raise ValueError('Embedding chưa normalize')
        qa[split].update(seconds=monitor.seconds, peak_process_rss_bytes=monitor.peak_rss_bytes,
                         peak_gpu_allocated_bytes=torch.cuda.max_memory_allocated(),
                         ordered_ids_hash=ordered_digest(frame.review_id.tolist()))
        np.save(cache / f'{split}_embeddings.npy', matrix, allow_pickle=False)
        np.save(cache / f'{split}_labels.npy', frame.label_id.to_numpy(dtype='int64'), allow_pickle=False)
        pd.DataFrame({'row_index': range(len(frame)), 'review_id': frame.review_id,
                      'text_sha256': [ordered_digest([t]) for t in texts]}).to_parquet(cache / f'{split}_mapping.parquet', index=False)
        frame[['review_id', 'parent_asin', 'asin', 'split', 'label_provenance']].to_parquet(cache / f'{split}_metadata.parquet', index=False)
        tokens = []
        for start in range(0, len(frame), 128):
            records = tokenizer.encode_batch(texts[start:start+128])
            for index, encoded in enumerate(records, start=start):
                tokens.append({'review_id': frame.review_id.iloc[index], 'label_id': int(frame.label_id.iloc[index]),
                    'input_ids': encoded.ids, 'attention_mask': encoded.attention_mask, 'token_type_ids': encoded.type_ids})
        pd.DataFrame(tokens).to_parquet(cache / f'{split}_transformer_tokens.parquet', index=False)
        print(f'PASS: {split} {matrix.shape}', flush=True)
    if identity != cache_identity(cfg, root):
        raise ValueError('Nguồn/cấu hình thay đổi trong lúc encode')
    metadata = {'status': 'PASS', 'identity': identity, 'embedding_model': enc['model'],
        'model_revision': enc['revision'], 'embedding_dimension': enc['dimension'],
        'pooling': enc['pooling'], 'normalization': enc['normalize_embeddings'], 'dtype': enc['dtype'],
        'batch_size': enc['batch_size'], 'device': enc['device'], 'seed': seed,
        'text_field_definition': TEXT_DEFINITION, 'dataset_hash': identity['dataset_hash'],
        'split_hash': identity['split_hash'], 'created_at': datetime.now(timezone.utc).isoformat(),
        'feature_columns': embedding_columns(enc['dimension']), 'qa': qa,
        'frozen': all(not p.requires_grad for p in model.parameters()), 'labels_used_by_encoder': False,
        'files_sha256': {p.name: sha256_file(p) for p in cache.iterdir() if p.is_file()}}
    write_json(cache / 'metadata.json', metadata)
    load_cache(cfg, root)
    report = ['# P4 — semantic representation', '', 'Trạng thái: PASS.', '',
        'Split cũ được giữ nguyên; toàn bộ ô nguồn so bằng nhau, không resplit. Kiểm tra ID/parent/variant/group/body/canonical text và lexical near-duplicate cross-split PASS.', '',
        f'Encoder frozen: {enc}. Không fit theo nhãn, không TF-IDF/BoW/SVD/PCA.', '',
        f'Sample train 128 review: {benchmark}.', '',
        'Chọn MiniLM vì kích thước 384 và chi phí đo trên GPU hiện có phù hợp. Không khẳng định encoder tốt nhất về sentiment; không dùng validation/test labels để chọn encoder. Giới hạn: review dài bị cắt ở 256 WordPiece; Transformer dùng tối đa 512 nên so sánh hai kiến trúc bao gồm khác biệt representation/context.', '',
        f'Cache: `{cfg["cache"]}`; embedding/labels/mapping/metadata/token BERT lưu riêng. BERT nhận canonical text qua tokenizer riêng, không dùng embedding.', '',
        'Cache identity gồm hash dataset, split, config, tokenizer. Loader kiểm tra hash từng tệp, row order, label và text hash. Config/dataset/split thay đổi sẽ bị từ chối; không âm thầm encode/overwrite.', '',
        f'QA từng split: {qa}. Sample replay và duplicate consistency PASS.', '',
        'Bằng chứng: `p4_semantic_split_validation.json`, `p4_encoder_benchmark.json` và cache metadata. Kiểm tra gần trùng là xấp xỉ từ vựng, không bảo đảm mọi paraphrase. Test cũ đã được đánh giá trong benchmark LEGACY; benchmark mới không phải test hoàn toàn chưa từng xem của toàn dự án.', '',
        'Giới hạn: chỉ laptop; proxy labels nhiễu; shift SemEval–Amazon trong laptop; gold thủ công nhỏ, hiện chưa có.']
    (root / 'reports/p4_semantic_representation.md').write_text('\n'.join(report) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
