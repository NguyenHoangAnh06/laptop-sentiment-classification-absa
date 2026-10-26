"""Bộ nhớ giới hạn có thể tái tạo P2 chỉ có trên Amazon; không có các tập đã chia, các mô hình hoặc SemEval."""

import csv
import hashlib
import json
import sqlite3
import time
from collections import Counter
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from src.data.acquisition import sha256_file
from src.data.cleaning import clean_review, quality_flags
from src.data.feasibility import check_memory, process_memory
from src.data.labeling import LABEL_TO_ID, noise_reasons, rating_label
from src.data.loader import iter_jsonl
from src.data.near_duplicates import audit_near_duplicates
from src.data.quality_audit import normalize_text, text_digest


def selection_key(review_id: str, seed: int) -> str:
    """Lựa chọn ổn định độc lập với đầu ra ratings/brand/model."""
    return hashlib.sha256(f'{seed}:{review_id}'.encode('utf-8')).hexdigest()


def load_qa_guards(paths: list[Path]) -> tuple[set[str], set[bytes]]:
    """Dự trữ ID QA nguồn và cả cụm văn bản chuẩn hóa old/new."""
    ids, keys = set(), set()
    for path in paths:
        with path.open(encoding='utf-8-sig', newline='') as handle:
            for row in csv.DictReader(handle):
                if row.get('review_id'):
                    ids.add(row['review_id'])
                    text = row['review_text']
                    keys.add(text_digest(normalize_text(text).casefold()))
                    keys.add(text_digest(clean_review(text).casefold()))
    return ids, keys


def stage_candidates(source: Path, database: Path, metadata: dict, *, seed: int,
                     qa_ids: set[str], qa_keys: set[bytes], max_memory: int,
                     max_seconds: int, max_output_bytes: int) -> dict:
    """Chuyển đổi luồng sang SQLite; giữ lại một sổ cái sắp xếp theo từng nguồn-hàng."""
    if database.exists():
        raise FileExistsError(database)
    started = time.monotonic()
    counts, flags, before_brands, before_labels = Counter(), Counter(), Counter(), Counter()
    with sqlite3.connect(database) as db:
        db.execute('PRAGMA cache_size=-16384')
        db.execute('PRAGMA temp_store=FILE')
        db.execute('CREATE TABLE groups (key BLOB PRIMARY KEY, n INTEGER, mask INTEGER, '
                   'product TEXT, user_key TEXT, cross_product INTEGER, cross_user INTEGER, '
                   'priority TEXT, payload TEXT)')
        db.execute('CREATE TABLE ledger (review_id TEXT PRIMARY KEY, text_key BLOB, outcome TEXT)')
        for index, row in iter_jsonl(source):
            counts['input_rows'] += 1
            reason, key = '', None
            try:
                label = rating_label(row.get('rating'))
                if (not isinstance(row.get('review_id'), str) or not row['review_id'].strip()
                        or not isinstance(row.get('text'), str) or row.get('parent_asin') not in metadata):
                    raise ValueError('Invalid identifiers/text/metadata linkage')
                brand = metadata[row['parent_asin']]['brand_normalized']
                before_brands[brand] += 1
                before_labels[label] += 1
                text = clean_review(row['text'])
                key = text_digest(text.casefold())
                row_flags = quality_flags(text)
                flags.update(row_flags)
                flags['changed_by_cleaning'] += text != row['text']
                if not text:
                    reason = 'empty_after_cleaning'
                elif '\ufffd' in text:
                    reason = 'unicode_replacement_quarantine'
                elif row['review_id'] in qa_ids or key in qa_keys or text_digest(normalize_text(row['text']).casefold()) in qa_keys:
                    reason = 'qa_id_or_text_reserved'
                elif ('unhandled_script_or_style' in row_flags
                      or 'low_lexical_diversity' in row_flags and 'repeated_character' in row_flags
                      or 'promotional_phrase' in row_flags and 'url_present_retained' in row_flags):
                    reason = 'spam_like_quarantine_unverified'
                else:
                    user = str(row.get('user_id') or '')
                    enriched = {**row, 'raw_text': row['text'], 'text': text,
                                'brand_raw': metadata[row['parent_asin']]['brand_raw'],
                                'brand_normalized': brand, 'sentiment': label, 'label_id': LABEL_TO_ID[label],
                                'label_provenance': 'rating-derived proxy', 'quality_flags': row_flags,
                                'clean_text_sha256': key.hex()}
                    db.execute('INSERT INTO groups VALUES (?,?,?, ?,?,0,0,?,?) '
                               'ON CONFLICT(key) DO UPDATE SET n=groups.n+1, mask=(groups.mask | excluded.mask), '
                               'cross_product=(groups.cross_product OR groups.product != excluded.product), '
                               'cross_user=(groups.cross_user OR groups.user_key != excluded.user_key)',
                               (key, 1, 1 << LABEL_TO_ID[label], row['parent_asin'],
                                hashlib.sha256(user.encode()).hexdigest() if user else '',
                                selection_key(row['review_id'], seed), json.dumps(enriched, ensure_ascii=False)))
                    reason = 'group_pending'
            except (ValueError, TypeError):
                reason = 'invalid_required_record'
            db.execute('INSERT INTO ledger VALUES (?,?,?)', (row.get('review_id', f'invalid:{index}'), key, reason))
            counts[reason] += 1
            if index % 10000 == 0:
                db.commit()
                check_memory(max_memory)
                if time.monotonic()-started > max_seconds or database.stat().st_size > max_output_bytes:
                    raise RuntimeError('P2 stage resource ceiling exceeded; incomplete output retained for diagnosis')
                print(f'P2 cleaning {index} source records', flush=True)
        db.commit()
        conflicts = db.execute('SELECT coalesce(sum(n),0) FROM groups WHERE mask NOT IN (1,2,4)').fetchone()[0]
        groups, rows, cross_product, cross_user = db.execute(
            'SELECT count(*),coalesce(sum(n),0),coalesce(sum(cross_product),0),coalesce(sum(cross_user),0) '
            'FROM groups WHERE mask IN (1,2,4)').fetchone()
        counts['mixed_proxy_label_group_rows_quarantined'] = conflicts
        counts['same_label_duplicate_excess_removed'] = rows-groups
        counts['eligible_unique_groups'] = groups
        accounted = (counts['input_rows']-counts['group_pending'] + conflicts + rows-groups + groups)
        if accounted != counts['input_rows']:
            raise ValueError('Row-count conservation failed')
        db.execute('CREATE INDEX priorities ON groups(priority)')
    return {'counts': dict(counts), 'flags': dict(flags), 'before_brands': dict(before_brands),
            'before_proxy_labels': dict(before_labels), 'cross_product_same_label_groups': cross_product,
            'cross_user_same_label_groups': cross_user, 'elapsed_seconds': time.monotonic()-started,
            'row_count_conservation': 'PASS',
            'dedup_policy': 'First saved-source row per cleaned/casefolded text; groups with conflicting sentiment proxy classes quarantined entirely. '
                            'QA ID/text reservations applied before dedup; no product-wide QA exclusion.'}


def select_english(database: Path, config: dict, *, max_memory: int) -> tuple[list[dict], dict]:
    """Đánh giá một danh sách rút gọn có giới hạn hạt giống; nhóm chưa được đánh giá không được khai báo tiếng Anh."""
    from lingua import Language, LanguageDetectorBuilder
    detector = LanguageDetectorBuilder.from_all_languages().with_low_accuracy_mode().build()
    accepted, outcomes = [], Counter()
    desired = config['target'] + config['noise_reserve'] + config['selection_buffer']
    limit, batch_size = config['max_language_candidates'], config['language_batch_size']
    started = time.monotonic()
    with sqlite3.connect(database) as db:
        db.execute('CREATE TABLE language_audit(review_id TEXT PRIMARY KEY, outcome TEXT, score REAL, margin REAL)')
        cursor = db.execute('SELECT payload FROM groups WHERE mask IN (1,2,4) ORDER BY priority LIMIT ?', (limit,))
        while batch := cursor.fetchmany(batch_size):
            rows = [json.loads(value[0]) for value in batch]
            scores = detector.compute_language_confidence_values_in_parallel([r['text'] for r in rows])
            for row, values in zip(rows, scores):
                # Mức giảm song song khác nhau ở mức ~1e-15; độ chính xác dự đoán (precision) chuẩn giúp ổn định các tệp kết quả.
                english_score = round(next((v.value for v in values if v.language == Language.ENGLISH), 0.), 8)
                margin = round(values[0].value-values[1].value if len(values) > 1 else values[0].value, 8)
                letters = [c for c in row['text'] if c.isalpha()]
                latin_share = sum(c.isascii() for c in letters)/len(letters) if letters else 0
                passed = (values[0].language == Language.ENGLISH and english_score >= config['english_min_score']
                          and margin >= config['language_min_margin'] and latin_share >= config['ascii_letter_min_share'])
                outcome = 'english_selected' if passed else 'language_uncertain_or_non_english'
                db.execute('INSERT INTO language_audit VALUES(?,?,?,?)', (row['review_id'], outcome, english_score, margin))
                outcomes[outcome] += 1
                if passed:
                    accepted.append({**row, 'language': 'en', 'language_detector_score': english_score})
            db.commit()
            check_memory(max_memory)
            if time.monotonic()-started > config['max_seconds']:
                raise RuntimeError('Language stage time ceiling exceeded')
            print(f'P2 language assessed {sum(outcomes.values())}; English selected {len(accepted)}', flush=True)
            if len(accepted) >= desired:
                break
    detector.unload_language_models()
    return accepted, {'outcomes': dict(outcomes), 'assessed': sum(outcomes.values()),
                      'elapsed_seconds': time.monotonic()-started,
                      'method': 'Lingua2.1.1 all75 languages, low-accuracy mode; full text; fixed score/margin/ASCII-letter gates. '
                                'Scores are detector-relative, not calibrated language probabilities. Seeded shortlist only; '
                                'mixed-language/short-text errors possible; no human language validation claim.'}


def reserve_noise(rows: list[dict], *, count: int, seed: int) -> tuple[list[dict], list[dict]]:
    """Lưu riêng các ứng cử viên chẩn đoán; không bao giờ sản xuất bộ gold do con người gán nhãn."""
    selected: dict = {}
    per_reason = max(1, count//3)
    reasons = ('five_star_negative_or_mixed_cue', 'low_star_positive_or_mixed_cue', 'low_star_neutral_cue')
    for reason in reasons:
        candidates = [r for r in rows if reason in noise_reasons(r['text'], r['rating'])]
        candidates.sort(key=lambda r: selection_key(r['review_id'], seed+1))
        for row in candidates[:per_reason]:
            selected[row['review_id']] = {**row, 'noise_candidate_reasons': noise_reasons(row['text'], row['rating']),
                                         'annotation_status': 'UNANNOTATED_DIAGNOSTIC_NOT_GOLD'}
    return [r for r in rows if r['review_id'] not in selected], list(selected.values())


def write_parquet(path: Path, rows: list[dict]) -> None:
    """Viết các hàng xác định bằng Mũi tên null/list suy luận rõ ràng từ các bản ghi."""
    if path.exists():
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pylist(rows)
    pq.write_table(table, path, compression='zstd')


def brand_summary(rows: list[dict]) -> dict:
    """Giữ review và quan điểm sản phẩm riêng biệt."""
    review_counts = Counter(r['brand_normalized'] for r in rows)
    product_map = {r['parent_asin']: r['brand_normalized'] for r in rows}
    return {'rows': len(rows), 'products': len(product_map), 'metadata_categories': len(review_counts),
            'review_counts': dict(review_counts), 'product_counts': dict(Counter(product_map.values())),
            'top5_review_share': sum(v for _,v in review_counts.most_common(5))/len(rows) if rows else None,
            'unknown_ambiguous_review_share': sum(review_counts[k] for k in ('UNKNOWN','AMBIGUOUS'))/len(rows) if rows else None}


def run_p2(config: dict, data_config: dict, *, root: Path) -> dict:
    """Thực thi lát cắt dọc chỉ được ủy quyền của Amazon; thất bại trên các đầu ra hiện có."""
    started = time.monotonic()
    output, clean_path = root/config['output_dir'], root/data_config['paths']['clean_reviews']
    if output.exists() or clean_path.exists():
        raise FileExistsError('Use new output paths; never overwrite an existing dataset/run')
    approval_path = root/'reports/tables/p1_owner_approval_20261009.json'
    approval = json.loads(approval_path.read_text(encoding='utf-8'))
    if not approval.get('p2_amazon_only_authorized') or approval.get('semeval_authorized'):
        raise ValueError('Missing bounded Amazon-only P2 approval')
    quality_path = root/config['quality_audit']
    quality = json.loads(quality_path.read_text(encoding='utf-8'))
    source = root/quality['source']
    if sha256_file(source) != quality['source_sha256']:
        raise ValueError('Saved quality audit/source mismatch')
    if data_config['rating_to_label'] != {1:'negative',2:'negative',3:'neutral',4:'positive',5:'positive'}:
        raise ValueError('Rating mapping changed')
    metadata_path = root/config['brand_products']
    with metadata_path.open(encoding='utf-8-sig', newline='') as handle:
        metadata = {r['product_id']:r for r in csv.DictReader(handle)}
    qa_paths = [root/p for p in quality['qa_sources']]
    for path in qa_paths:
        if sha256_file(path) != quality['qa_sources'][path.relative_to(root).as_posix()]:
            raise ValueError('Frozen QA source changed')
    qa_ids, qa_keys = load_qa_guards(qa_paths)
    output.mkdir(parents=True)
    (output/'STATUS.txt').write_text('IN_PROGRESS; outputs are not completed until manifest.json exists\n', encoding='utf-8')
    database = output/'candidate_ledger.sqlite'
    stage = stage_candidates(source, database, metadata, seed=data_config['seed'], qa_ids=qa_ids,
                             qa_keys=qa_keys, max_memory=config['max_memory_bytes'],
                             max_seconds=config['max_seconds'], max_output_bytes=config['max_output_bytes'])
    if stage['counts']['input_rows'] != quality['rows']:
        raise ValueError('Candidate count differs from reused audit')
    config = {**config, 'target': data_config['target_clean_reviews']}
    english, language = select_english(database, config, max_memory=config['max_memory_bytes'])
    pool, noise = reserve_noise(english, count=config['noise_reserve'], seed=data_config['seed'])
    selected, product_counts, cap_removed = [], Counter(), 0
    for row in pool:
        product = row['parent_asin']
        if product_counts[product] >= config['max_reviews_per_product']:
            cap_removed += 1
            continue
        selected.append(row)
        product_counts[product] += 1
        if len(selected) == config['target']:
            break
    if not selected or {r['sentiment'] for r in selected} != set(LABEL_TO_ID):
        raise ValueError('Empty clean selection or missing sentiment class; assess adequacy before completion')
    # Loại bỏ các cụm văn bản chẩn đoán nhiễu khỏi vùng chọn đã xử lý.
    assert not {r['clean_text_sha256'] for r in noise} & {r['clean_text_sha256'] for r in selected}
    pairs, near = audit_near_duplicates(selected+noise, seed=data_config['seed'],
                                        threshold=config['near_jaccard'], max_comparisons=config['max_near_comparisons'])
    # Các nhóm gần chạm vào chẩn đoán dành riêng cũng phải tránh xa các ứng cử viên huấn luyện.
    reserved_groups = {r['near_duplicate_group_id'] for r in noise if r['near_duplicate_group_id']}
    near_reserved = [r for r in selected if r['near_duplicate_group_id'] in reserved_groups]
    selected = [r for r in selected if r['near_duplicate_group_id'] not in reserved_groups]
    labels = Counter(r['sentiment'] for r in selected)
    if sha256_file(source) != quality['source_sha256']:
        raise ValueError('Input bytes changed during processing')
    check_memory(config['max_memory_bytes'])
    write_parquet(clean_path, selected)
    if noise:
        write_parquet(output/'label_noise_candidates.parquet', noise)
        columns = ['review_id','parent_asin','brand_normalized','rating','sentiment','text','raw_text',
                   'noise_candidate_reasons','annotation_status']
        with (output/'label_noise_candidates.csv').open('x',encoding='utf-8-sig',newline='') as handle:
            writer = csv.DictWriter(handle, fieldnames=columns)
            writer.writeheader()
            for row in noise:
                writer.writerow({k: json.dumps(row[k]) if isinstance(row[k],list) else row[k] for k in columns})
    (output/'near_duplicate_pairs.json').write_text(json.dumps(pairs,indent=2)+'\n',encoding='utf-8')
    final = pq.read_table(clean_path, columns=['review_id','clean_text_sha256','sentiment','label_id','text']).to_pylist()
    if (len(final) != len(selected) or len({r['review_id'] for r in final}) != len(final)
            or len({r['clean_text_sha256'] for r in final}) != len(final)
            or any(r['label_id'] != LABEL_TO_ID[r['sentiment']] or not r['text'].strip() for r in final)):
        raise ValueError('Persisted clean dataset contract failed')
    result = {'version':'p2_amazon_only_v1', 'approval_sha256':sha256_file(approval_path), 'seed':data_config['seed'],
              'configuration':config, 'configuration_sha256':hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest(),
              'source_sha256':quality['source_sha256'], 'reused_quality_audit_sha256':sha256_file(quality_path),
              'brand_metadata_sha256':sha256_file(metadata_path), 'qa_sources':quality['qa_sources'],
              'stage':stage, 'language':language, 'near_duplicates':near,
              'selection':{'target':config['target'],'actual':len(selected),'noise_reserved':len(noise),
                           'product_cap_skips_before_target':cap_removed,'near_noise_cluster_reservations':len(near_reserved),
                           'method':'Seed42 review-ID hash order over cleaned unique eligible groups, bounded language shortlist, '
                                    'diagnostic reservations and product cap100; no label/brand balancing, no train/validation/test split'},
              'proxy_counts':dict(labels), 'proxy_percentages':{k:100*v/len(selected) for k,v in labels.items()},
              'largest_minority_ratio':max(labels.values())/min(labels.values()),
              'imbalance_policy':'Compare unweighted vs class-weighted baselines on validation at P5/P6; no resampling or weights fitted/chosen in P2.',
              'brand_before':{'rows':stage['counts']['input_rows'],'review_counts':stage['before_brands']},
              'brand_after':brand_summary(selected),'noise_reason_counts':dict(Counter(reason for r in noise for reason in r['noise_candidate_reasons'])),
              'validation':'PASS: row conservation, QA reservations, duplicate-ID/text disjointness, raw bytes unchanged, parquet labels/IDs/text',
              'clean_parquet_sha256':sha256_file(clean_path),'resources':process_memory(),
              'implementation_sha256':{name:sha256_file(Path(__file__).parent/name)
                                       for name in ('p2_pipeline.py','cleaning.py','labeling.py','near_duplicates.py')},
              'dependencies':{'pyarrow':'23.0.1','lingua-language-detector':'2.1.1','numpy':'2.2.6'},
              'elapsed_seconds':time.monotonic()-started,'semeval_status':'BLOCKED; never read/used by P2',
              'splits_created':False,'models_trained':False,'gold_labels_created':False,
              'limitations':'Selected laptop pool, recall89.0767% joint95% CI55.4584–99.8455%; selection bias and assisted-QA '
                            'independence limits retained. Automated language/spam/noise heuristics not human verification. '
                            'Near duplicates are lexical candidate search, not exhaustive semantic proof. Rating proxy noise; '
                            'SemEval-to-Amazon laptop platform/style shift; small independent human gold still pending.'}
    (output/'manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (output/'STATUS.txt').write_text('COMPLETE: pipeline executed; remaining scientific limitations in manifest\n',encoding='utf-8')
    return result
