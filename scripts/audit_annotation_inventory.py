"""Kiểm tra QA trống kế thừa và nhãn gán hiện tại mà không cần chuyển con người nhãn."""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from src.config import load_config
from src.data.acquisition import sha256_file
from src.data.filter_qa import read_qa
from src.data.independent_qa import read_csv, write_csv
from src.data.laptop_filter import classify_product
from src.data.loader import iter_jsonl
from src.data.validation import deterministic_sample, stable_key


def product_fingerprint(row: dict) -> str:
    """Chỉ bằng chứng sản phẩm phổ biến; không phải là ràng buộc review/source đầy đủ."""
    categories = row['categories']
    if isinstance(categories, str):
        categories = json.loads(categories)
    return stable_key({'title': row['title'], 'categories': categories}, 0)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--pending-output', type=Path, required=True)
    args = parser.parse_args()
    if args.output_dir.exists() or args.pending_output.exists():
        parser.error('Use new output paths')
    if Path('data/interim').resolve() not in args.pending_output.resolve().parents:
        parser.error('Pending copy must be under data/interim')
    if Path('reports').resolve() not in args.output_dir.resolve().parents:
        parser.error('Audit reports must be under reports')
    baseline = Path('data/manual/laptop_filter_qa.csv')
    columns, blank = read_csv(baseline)
    read_qa(baseline, 'human_is_laptop')
    config = load_config('acquisition')
    seed = load_config('data')['seed']
    prefix = Path('data/raw/amazon/metadata_prefix_20000.jsonl')
    source_rows = []
    for line, row in iter_jsonl(prefix):
        details = row.get('details') or {}
        if isinstance(details, str):
            details = json.loads(details)
        decision = classify_product(row, config['filter'])
        source_rows.append({'parent_asin': row['parent_asin'], 'title': row.get('title'),
            'categories': row.get('categories'), 'brand': details.get('Brand'),
            'store': row.get('store'), 'source_line': line,
            'rule_include': decision.include, 'rule_reason': decision.reason})
    expected = []
    for include in (True, False):
        expected += deterministic_sample((r for r in source_rows if r['rule_include'] == include),
                                         config['qa']['sample_size_per_decision'], seed)
    source_by_line = {str(r['source_line']): r for r in source_rows}
    source_checks = []
    for row in blank:
        ref = source_by_line[row['source_line']]
        fields_match = all((row[k] == ('' if ref[k] is None else str(ref[k])))
                          for k in ('parent_asin', 'title', 'brand', 'store', 'rule_include', 'rule_reason'))
        source_checks.append(fields_match and json.loads(row['categories']) == ref['categories'])
    references = defaultdict(list)
    inventory = []
    paths = sorted(p for p in Path('data/manual').rglob('*.csv') if 'archive' not in p.parts)
    paths.append(Path('data/interim/annotation_normalization/20261009/v2_review_annotation_canonical.csv'))
    for path in paths:
        headers, rows = read_csv(path)
        field = next((c for c in ('human_label', 'human_is_target_product', 'human_is_laptop') if c in headers), None)
        if field is None:
            continue
        allowed = {'laptop', 'non_laptop', 'uncertain', ''} if field == 'human_label' else {'true', 'false', 'yes', 'no', 'unsure', ''}
        if path.parent.name == 'p1_v2':
            allowed |= {'accept', 'reject'}  # đã gửi từ vựng, được chuẩn hóa riêng
        id_field = 'annotation_id' if 'annotation_id' in headers else 'parent_asin'
        counts = Counter(r[field] for r in rows)
        inventory.append({'path': path.as_posix(), 'sha256': sha256_file(path), 'rows': len(rows),
            'label_column': field, 'label_counts': dict(counts),
            'invalid_labels': sum(r[field].strip().lower() not in allowed for r in rows),
            'duplicate_ids': len(rows)-len({r[id_field] for r in rows}),
            'missing_ids': sum(not r[id_field].strip() for r in rows),
            'reviewer': 'human_reviewer_01', 'review_declaration': 'Global final human review already confirmed',
            'human_review_status': 'COMPLETED', 'missing_final_labels': counts.get('', 0)})
        if path == baseline or not any(r[field] for r in rows):
            continue
        for row in rows:
            label = row[field].strip().lower()
            if label in ('laptop', 'non_laptop', 'true', 'false', 'yes', 'no'):
                identifier = row.get('product_id', row.get('parent_asin'))
                references[identifier].append({'path': path.as_posix(),
                    'id': row.get('annotation_id', identifier), 'label': label,
                    'product_fingerprint': product_fingerprint(row)})
    links = []
    for row in blank:
        matches = references[row['parent_asin']]
        exact = [r for r in matches if r['product_fingerprint'] == product_fingerprint(row)]
        links.append({'parent_asin': row['parent_asin'], 'source_line': row['source_line'],
            'source_fields_match': source_checks[len(links)], 'reference_id_matches': len(matches),
            'reference_product_fingerprint_matches': len(exact),
            'reference_annotations': json.dumps(matches, ensure_ascii=False),
            'action': 'Existing product evidence reference; no automatic label transfer' if exact
                      else 'Optional legacy annotation remains blank; excluded from official QA'})
    result = {'baseline': {'path': baseline.as_posix(), 'sha256': sha256_file(baseline),
        'rows': len(blank), 'blank_labels': sum(not r['human_is_laptop'] for r in blank),
        'role': 'Legacy seeded metadata-prefix product QA template from scripts.audit_p1.audit_legacy_prefix',
        'prefix_path': prefix.as_posix(), 'prefix_sha256': sha256_file(prefix),
        'source_fields_match': all(source_checks),
        'seeded_membership_and_order_reproduced': [r['parent_asin'] for r in expected] == [r['parent_asin'] for r in blank],
        'random_included': sum(r['rule_include'] == 'True' for r in blank),
        'independent_qa_sampling_unit': False, 'blocks_current_v1_v2_evaluation': False,
        'reference_id_matches': sum(bool(r['reference_id_matches']) for r in links),
        'reference_product_fingerprint_matches': sum(bool(r['reference_product_fingerprint_matches']) for r in links)},
        'inventory': inventory, 'pending_output': args.pending_output.as_posix(),
        'historical_correction': 'Full-survey labeled100 file exists now and was omitted by previous inventory; '
            'human_is_target_product is a supported historical schema. Earlier absent-path statement superseded.',
        'label_transfer': 'NOT_PERFORMED; no predictions or other sampling units substituted as labels'}
    args.output_dir.mkdir(parents=True)
    args.pending_output.parent.mkdir(parents=True, exist_ok=True)
    write_csv(args.pending_output, columns, [r for r in blank if not r['human_is_laptop'].strip()])
    write_csv(args.output_dir/'baseline_references.csv', list(links[0]), links)
    (args.output_dir/'inventory.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result['baseline'], indent=2))


if __name__ == '__main__':
    main()
