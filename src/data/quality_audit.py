"""Kiểm tra nhóm ứng viên chỉ đọc; không dán nhãn lại phạm vi hoặc lựa chọn huấn luyện cuối cùng."""

import hashlib
import html
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from src.data.feasibility import check_memory, process_memory
from src.data.loader import iter_jsonl


def normalize_text(text: str) -> str:
    """Giải mã HTML và thu gọn khoảng trắng; bảo quản trường hợp, dấu câu và phủ định."""
    return ' '.join(html.unescape(text).split())


def text_digest(text: str) -> bytes:
    return hashlib.sha256(text.encode('utf-8')).digest()


def _cluster_add(groups: dict, key: bytes, parent: str, rating: int, variant: bytes) -> None:
    if key not in groups:
        groups[key] = [1, parent, False, 1 << rating, variant, False]
    else:
        state = groups[key]
        state[0] += 1
        state[2] |= state[1] != parent
        state[3] |= 1 << rating
        state[5] |= state[4] != variant


def _summary(groups: dict) -> dict:
    repeated = [v for v in groups.values() if v[0] > 1]
    return {'unique_keys': len(groups), 'duplicate_groups': len(repeated),
            'duplicate_excess_rows': sum(v[0]-1 for v in repeated),
            'rows_in_duplicate_groups': sum(v[0] for v in repeated),
            'cross_product_groups': sum(v[2] for v in repeated),
            'mixed_rating_groups': sum(v[3].bit_count() > 1 for v in repeated),
            'distinct_text_variant_groups': sum(v[5] for v in repeated)}


def audit_review_pool(path: Path, *, qa_review_ids: set[str], qa_product_ids: set[str],
                      qa_text_keys: set[bytes], max_memory_bytes: int = 512_000_000) -> tuple[dict, list[dict]]:
    """Truyền phát tất cả các ứng cử viên đã lưu; báo cáo các cụm trùng lặp và rủi ro QA rò rỉ dữ liệu."""
    missing, types, word_hist, char_hist, by_label = Counter(), Counter(), Counter(), Counter(), Counter()
    raw_groups, normalized_groups, loose_groups = {}, {}, {}
    identifiers = set()
    date_min = date_max = None
    flags = Counter()
    required = ('review_id', 'parent_asin', 'text', 'rating')
    optional = ('asin', 'user_id', 'review_title', 'timestamp', 'helpful_vote', 'verified_purchase')
    rows = 0
    rating_map = {1: 'negative', 2: 'negative', 3: 'neutral', 4: 'positive', 5: 'positive'}
    for _, row in iter_jsonl(path):
        rows += 1
        for field in required + optional:
            value = row.get(field)
            missing[field] += value is None or isinstance(value, str) and not value.strip()
            types[f'{field}:{type(value).__name__}'] += 1
        text, rating, parent, review_id = (row.get(k) for k in ('text', 'rating', 'parent_asin', 'review_id'))
        if (not isinstance(text, str) or not isinstance(parent, str) or not parent
                or not isinstance(review_id, str) or not review_id or type(rating) is not int
                or rating not in rating_map):
            flags['invalid_required_record'] += 1
            continue
        identifier = text_digest(review_id)
        flags['duplicate_review_id_rows'] += identifier in identifiers
        identifiers.add(identifier)
        normalized = normalize_text(text)
        words = len(normalized.split())
        word_hist[words] += 1
        char_hist[len(text)] += 1
        by_label[rating_map[rating]] += 1
        flags['empty_normalized_text'] += not normalized
        flags['short_under_5_words'] += words < 5
        flags['html_entity_candidate'] += bool(re.search(r'&(?:#\d+|#x[0-9a-fA-F]+|\w+);', text))
        flags['html_tag_candidate'] += bool(re.search(r'<\s*/?\s*[A-Za-z][^>]*>', text))
        flags['url_candidate'] += bool(re.search(r'https?://|www\.', text, re.I))
        flags['unicode_replacement_character'] += '\ufffd' in text
        flags['normalization_would_change_text'] += normalized != text
        strict = text_digest(normalized.casefold())
        raw = text_digest(text)
        loose = text_digest(re.sub(r'[^\w]+', ' ', normalized.casefold()).strip())
        _cluster_add(raw_groups, raw, parent, rating, raw)
        _cluster_add(normalized_groups, strict, parent, rating, raw)
        _cluster_add(loose_groups, loose, parent, rating, strict)
        flags['qa_review_id_rows'] += review_id in qa_review_ids
        flags['qa_product_rows'] += parent in qa_product_ids
        flags['qa_normalized_text_rows'] += strict in qa_text_keys
        if review_id in qa_review_ids or strict in qa_text_keys:
            flags['qa_id_or_text_rows'] += 1
        timestamp = row.get('timestamp')
        if isinstance(timestamp, (int, float)) and not isinstance(timestamp, bool):
            try:
                date = datetime.fromtimestamp(timestamp/1000, timezone.utc).isoformat()
                date_min = min(date_min, date) if date_min else date
                date_max = max(date_max, date) if date_max else date
            except (ValueError, OverflowError, OSError):
                flags['invalid_timestamp'] += 1
        elif timestamp is not None:
            flags['invalid_timestamp'] += 1
        if rows % 10000 == 0:
            check_memory(max_memory_bytes)
    check_memory(max_memory_bytes)
    def quantiles(hist: Counter) -> dict:
        result = {}
        for name, fraction in [('p50', .5), ('p90', .9), ('p95', .95), ('p99', .99)]:
            cumulative = 0
            target = max(1, int(sum(hist.values())*fraction + .999999))
            for value, count in sorted(hist.items()):
                cumulative += count
                if cumulative >= target:
                    result[name] = value
                    break
        return result
    clusters = [{'normalization': kind, 'text_sha256': key.hex(), 'rows': state[0],
                 'cross_product': state[2], 'mixed_ratings': state[3].bit_count() > 1,
                 'different_text_variants': state[5]}
                for kind, groups in [('raw_exact', raw_groups), ('html_whitespace_casefold', normalized_groups),
                                     ('punctuation_candidate', loose_groups)]
                for key, state in sorted(groups.items()) if state[0] > 1]
    result = {'rows': rows, 'missing_by_field': dict(missing), 'observed_types': dict(types),
        'flags': dict(flags), 'raw_exact_duplicates': _summary(raw_groups),
        'normalized_duplicates': _summary(normalized_groups), 'punctuation_candidates': _summary(loose_groups),
        'word_length_quantiles': quantiles(word_hist), 'character_length_quantiles': quantiles(char_hist),
        'word_length_distribution': dict(sorted(word_hist.items())),
        'rating_proxy_class_counts': dict(by_label), 'label_provenance': 'rating-derived proxy',
        'timestamp_min_utc': date_min, 'timestamp_max_utc': date_max,
        'resources': process_memory(), 'training_dataset_created': False,
        'language_validity': 'NOT_MEASURED; no language detection or clean-English claim',
        'method': 'Read-only original candidates. Normalization for duplicate keys only; no rows changed/deleted. '
            'Punctuation candidates are not semantic near-duplicate proof; no automatic removal. '
            'Mixed ratings are quality flags, not human sentiment disagreement measurements.',
        'split_status': 'NOT_CREATED; prevent QA ID/text leakage and duplicate clusters before fixed splits'}
    return result, clusters
