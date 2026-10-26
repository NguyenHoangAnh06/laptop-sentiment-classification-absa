"""Kiểm tra đã gửi v2 nhãn gán mà không thay đổi nhãn hoặc khai báo con người review."""

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

from src.data.acquisition import sha256_file
from src.data.independent_qa import (
    ERROR_REASONS, LABELS, REVIEW_COLUMNS, fixed_fingerprint, read_csv, write_csv,
)
from src.data.supplemental_qa import frozen_pilot


def audit_annotations(kit: Path) -> tuple[dict, list[dict]]:
    """Kiểm tra các ràng buộc bất biến và thu thập tất cả các vấn đề về trường con người mà không cần sửa chữa."""
    manifest = json.loads((kit / 'manifest.json').read_text(encoding='utf-8'))
    columns, rows = read_csv(kit / 'review_annotation.csv')
    refs = json.loads((kit / 'private_predictions.json').read_text(encoding='utf-8'))
    by_id = {row['annotation_id']: row for row in refs}
    pilot_kit = Path(manifest['pilot_kit'])
    pilot_eval = Path(manifest['pilot_evaluation'])
    _, old, pilot_rows = frozen_pilot(pilot_kit, pilot_eval)
    population = manifest['populations']['reject_complement']
    n = manifest['sample_size']
    annotation_ids = Counter(row['annotation_id'] for row in rows)
    review_ids = Counter(row['review_id'] for row in rows)
    checks = {
        'schema': columns == REVIEW_COLUMNS,
        'sample_count': len(rows) == n == len(refs),
        'unique_annotation_ids': all(v == 1 for v in annotation_ids.values()),
        'unique_review_ids': all(v == 1 for v in review_ids.values()),
        'original_sample_ids': set(annotation_ids) == set(by_id) and len(by_id) == len(refs),
        'immutable_source_fields': all(
            row['annotation_id'] in by_id and
            fixed_fingerprint(row) == by_id[row['annotation_id']]['fixed_fingerprint']
            for row in rows),
        'no_v1_overlap': not (set(review_ids) & {r['review_id'] for r in pilot_rows}),
        'sidecar_checksum': sha256_file(kit / 'private_predictions.json') ==
            manifest['files']['private_predictions.json']['sha256'],
        'pilot_evaluation_checksum': sha256_file(pilot_eval) == manifest['pilot_evaluation_sha256'],
        'pilot_manifest_checksum': sha256_file(pilot_kit / 'manifest.json') == manifest['pilot_manifest_sha256'],
        'sampling_design': population == old['strata']['review:random_reject']['frame_population'] -
            old['strata']['review:random_reject']['sample_size'] and all(
                ref['prediction'] is False and ref['stratum'] == 'random_reject_complement' and
                ref['sample_size'] == n and ref['frame_population'] == population and
                math.isclose(ref['inclusion_probability'], n / population) and
                math.isclose(ref['sampling_weight'], population / n) for ref in refs),
    }
    issues = []
    product_labels = defaultdict(set)
    for row in old['comparisons']:
        if row['human_label'] in ('laptop', 'non_laptop'):
            product_labels[row['product_id']].add(row['human_label'])
    for line, row in enumerate(rows, 2):
        reasons = []
        label = row['human_label'].strip().lower()
        if label not in LABELS:
            reasons.append('invalid_label_enum')
        elif not label or label == 'uncertain':
            reasons.append('unresolved_label')
        if label and not row['human_evidence'].strip():
            reasons.append('missing_evidence')
        if row['human_error_reason'].strip() not in ERROR_REASONS:
            reasons.append('invalid_error_reason_enum')
        if label in ('laptop', 'non_laptop'):
            product_labels[row['product_id']].add(label)
        if reasons:
            issues.append({'csv_line': line, 'annotation_id': row['annotation_id'],
                           'review_id': row['review_id'], 'human_label': row['human_label'],
                           'issues': '|'.join(reasons)})
    conflicts = sorted(p for p, labels in product_labels.items() if len(labels) > 1)
    return {
        'status': 'READY_FOR_REVIEWER_DECLARATION' if all(checks.values()) and not issues and not conflicts
            else 'BLOCKED_VALIDATION',
        'annotation_sha256': sha256_file(kit / 'review_annotation.csv'),
        'rows': len(rows), 'encoding': 'strict UTF-8 (optional BOM)',
        'types': 'CSV fields preserved as strings, including all IDs',
        'checks': checks, 'submitted_label_counts': dict(Counter(r['human_label'] for r in rows)),
        'missing_values_by_column': {c: sum(not r[c].strip() for r in rows) for c in columns},
        'issue_rows': len(issues), 'conflicting_canonical_product_labels': conflicts,
        'label_mapping': 'NOT_APPLIED; ACCEPT/REJECT require user interpretation confirmation',
        'official_evaluation': 'NOT_RUN; human reviewer identity/process declaration required',
    }, issues


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kit-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    if args.output_dir.exists():
        parser.error('Use a new output directory')
    output = args.output_dir.resolve()
    for source in (Path('data'), Path('src'), Path('configs'), Path('tests')):
        protected = source.resolve()
        if output == protected or protected in output.parents or output in protected.parents:
            parser.error('Output must be separate from source/data directories')
    result, issues = audit_annotations(args.kit_dir)
    args.output_dir.mkdir(parents=True)
    (args.output_dir / 'validation.json').write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    write_csv(args.output_dir / 'annotation_issues.csv',
              ['csv_line', 'annotation_id', 'review_id', 'human_label', 'issues'], issues)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
