"""Ghi lại review của chủ dự án và tạo bản sao v2 chuẩn, bảo quản bản gốc."""

import argparse
import json
from collections import Counter
from pathlib import Path

from src.data.acquisition import sha256_file
from src.data.independent_qa import fixed_fingerprint, read_csv, write_csv


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--canonical-output', type=Path, required=True)
    parser.add_argument('--annotator', default='human_reviewer_01')
    parser.add_argument('--confirm-human-review', action='store_true')
    args = parser.parse_args()
    if not args.confirm_human_review or not args.annotator.strip():
        parser.error('Actual human review declaration and reviewer ID required')
    if args.output_dir.exists():
        parser.error('Use a new output directory')
    canonical_root = Path('data/interim').resolve()
    if canonical_root not in args.canonical_output.resolve().parents or args.canonical_output.exists():
        parser.error('Canonical output must be a new file under data/interim')
    root = Path('data/manual').resolve()
    output = args.output_dir.resolve()
    if output == root or root in output.parents or output in root.parents:
        parser.error('Use an output directory outside original manual annotations')
    files = sorted(p for p in Path('data/manual').rglob('*.csv') if 'archive' not in p.parts)
    records = []
    canonical = None
    for path in files:
        columns, rows = read_csv(path)
        label_column = next((c for c in ('human_label', 'human_is_laptop', 'human_is_target_product')
                             if c in columns), None)
        if label_column is None:
            continue
        historical = ('human_verified_after_ai_assistance' if 'p1_v1' in path.parts
                      else 'unspecified')
        records.append({
            'path': path.as_posix(), 'sha256': sha256_file(path), 'rows': len(rows),
            'annotator': args.annotator, 'human_verified': True,
            'human_review_status': 'COMPLETED', 'review_status': 'APPROVED',
            'review_status_scope': 'label approval only; not QA or phase acceptance',
            'label_provenance': historical,
            'provenance_note': 'Project owner declares final review of all existing annotations. '
                'Prior history retained; unspecified does not mean no AI assistance.',
            'label_counts': dict(Counter(row[label_column] for row in rows)),
            'missing_final_labels': sum(not row[label_column].strip() for row in rows),
        })
        if path == Path('data/manual/independent_qa/p1_v2/review_annotation.csv'):
            mapping = {'ACCEPT': 'laptop', 'REJECT': 'non_laptop'}
            normalized = []
            for row in rows:
                copy = dict(row)
                label = copy['human_label'].strip()
                if label in mapping:
                    copy['human_label'] = mapping[label]
                elif label not in {'laptop', 'non_laptop', 'uncertain', ''}:
                    raise ValueError(f'Unsupported submitted label: {label}')
                if fixed_fingerprint(copy) != fixed_fingerprint(row):
                    raise ValueError('Source fields changed')
                normalized.append(copy)
            canonical = (columns, normalized, path, mapping)
    if canonical is None:
        raise ValueError('V2 submission not found')
    args.output_dir.mkdir(parents=True)
    columns, rows, source, mapping = canonical
    target = args.canonical_output
    target.parent.mkdir(parents=True, exist_ok=True)
    write_csv(target, columns, rows)
    result = {
        'review_declaration_date': '2026-10-09 Asia/Saigon',
        'reviewer_id_mapping': 'reviewer_id mapped to existing annotator human_reviewer_01',
        'storage': 'Review metadata sidecar; existing annotation CSV schemas unchanged',
        'annotations': records,
        'canonical_v2': {'source': source.as_posix(), 'source_sha256': sha256_file(source),
            'path': target.as_posix(), 'sha256': sha256_file(target),
            'mapping': mapping, 'mapping_basis': 'Domain ACCEPT/REJECT convention under user request '
                'to normalize annotations; no filter prediction used.',
            'labels': dict(Counter(row['human_label'] for row in rows)),
            'original_source_fields_preserved': True},
        'qa_acceptance': 'NEEDS REVIEW', 'phase_acceptance': 'NOT APPROVED',
        'ai_assistance_v2': 'Not specified by latest declaration; do not claim independent/blind',
    }
    (args.output_dir/'review_confirmation.json').write_text(
        json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    for record in records:
        if sha256_file(Path(record['path'])) != record['sha256']:
            raise ValueError('Original annotation changed during recording')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
