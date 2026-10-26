"""Kiểm tra từ vựng gần như trùng lặp bị ràng buộc; không có nhận dạng ngữ nghĩa hoặc xóa tự động."""

import hashlib
import re
from collections import defaultdict

import numpy as np


def shingles(text: str) -> set[int]:
    """Băm ba từ liên tiếp, giữ nguyên phủ định token."""
    words = re.findall(r"\w+(?:['’]\w+)?", text.casefold())
    if len(words) < 10:
        return set()
    return {int.from_bytes(hashlib.blake2b(' '.join(words[i:i+3]).encode('utf-8'),
                                         digest_size=8).digest(), 'little')
            for i in range(len(words)-2)}


def audit_near_duplicates(rows: list[dict], *, seed: int, threshold: float = .9,
                          max_comparisons: int = 100000) -> tuple[list[dict], dict]:
    """Các ứng cử viên MinHash LSH theo sau là kiểm tra Jaccard băm chính xác."""
    rng = np.random.default_rng(seed)
    multipliers = rng.integers(1, 2**63, size=32, dtype=np.uint64) | np.uint64(1)
    offsets = rng.integers(0, 2**63, size=32, dtype=np.uint64)
    buckets: dict = defaultdict(list)
    parents = list(range(len(rows)))
    pairs, comparisons, capped = [], 0, False

    def root(index: int) -> int:
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    for index, row in enumerate(rows):
        values = shingles(row['text'])
        if not values:
            continue
        hashes = np.array(sorted(values), dtype=np.uint64)
        with np.errstate(over='ignore'):
            signature = (hashes[:, None] * multipliers + offsets).min(axis=0)
        keys = [(band, signature[4*band:4*band+4].tobytes()) for band in range(8)]
        candidates = sorted({other for key in keys for other in buckets[key]})
        for other in candidates:
            if comparisons >= max_comparisons:
                capped = True
                break
            comparisons += 1
            previous = shingles(rows[other]['text'])
            similarity = len(values & previous) / len(values | previous)
            if similarity >= threshold:
                left, right = root(index), root(other)
                parents[max(left, right)] = min(left, right)
                pairs.append({'review_id_a': rows[other]['review_id'], 'review_id_b': row['review_id'],
                              'jaccard': similarity, 'same_proxy_label': row['sentiment'] == rows[other]['sentiment']})
        for key in keys:
            buckets[key].append(index)
        if capped:
            break
    counts = defaultdict(int)
    for index in range(len(rows)):
        counts[root(index)] += 1
    for index, row in enumerate(rows):
        group = root(index)
        row['near_duplicate_group_id'] = rows[group]['review_id'] if counts[group] > 1 else None
    return pairs, {'method': '32 stable uint64 MinHash components,8 bands x4; exact hashed word-triple Jaccard>=threshold',
                   'threshold': threshold, 'comparisons': comparisons, 'pairs': len(pairs),
                   'groups': sum(n > 1 for n in counts.values()), 'comparison_cap_reached': capped,
                   'limits': 'Lexical approximate candidate search, not exhaustive semantic detection. Short<10word texts skipped. '
                             'Pairs retained with group IDs for P4 leakage control; no sentiment-changing near-dedup deletion.'}
