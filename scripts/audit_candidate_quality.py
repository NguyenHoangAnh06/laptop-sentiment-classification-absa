"""Kiểm toán đã lưu các ứng viên laptop một cách độc lập với các quyết định chấp nhận còn tồn đọng."""

import argparse
import json
import time
from pathlib import Path

from src.data.acquisition import sha256_file
from src.data.independent_qa import read_csv, write_csv
from src.data.quality_audit import audit_review_pool, normalize_text, text_digest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--clusters-output', type=Path, required=True)
    args = parser.parse_args()
    if args.output_dir.exists() or args.clusters_output.exists():
        parser.error('Use new output paths')
    if Path('reports').resolve() not in args.output_dir.resolve().parents:
        parser.error('Reports must be under reports')
    if Path('data/interim').resolve() not in args.clusters_output.resolve().parents:
        parser.error('Clusters must be under data/interim')
    report = json.loads((args.run_dir/'report.json').read_text(encoding='utf-8'))
    pool = args.run_dir/'laptop_valid.jsonl'
    pool_hash = sha256_file(pool)
    if pool_hash != report['output_sha256']['laptop_valid.jsonl']:
        raise ValueError('Candidate pool checksum differs from saved run')
    qa_ids, qa_products, qa_keys = set(), set(), set()
    paths = [Path('data/manual/independent_qa/p1_v1/product_annotation.csv'),
             Path('data/manual/independent_qa/p1_v1/review_annotation.csv'),
             Path('data/interim/annotation_normalization/20261009/v2_review_annotation_canonical.csv'),
             Path('data/manual/feasibility/Electronics_laptop_3aeb96dfe815.csv')]
    for path in paths:
        _, rows = read_csv(path)
        qa_products.update(r.get('product_id', r.get('parent_asin')) for r in rows)
        for row in rows:
            if row.get('review_id'):
                qa_ids.add(row['review_id'])
                qa_keys.add(text_digest(normalize_text(row['review_text']).casefold()))
    started = time.monotonic()
    result, clusters = audit_review_pool(pool, qa_review_ids=qa_ids,
        qa_product_ids=qa_products, qa_text_keys=qa_keys)
    if result['rows'] != report['groups']['laptop']['valid_reviews']:
        raise ValueError('Candidate count differs from saved run')
    result.update(source=pool.as_posix(), source_sha256=pool_hash,
        run_report_sha256=sha256_file(args.run_dir/'report.json'),
        elapsed_seconds=time.monotonic()-started,
        qa_sources={p.as_posix(): sha256_file(p) for p in paths},
        qa_guard_sizes={'review_ids':len(qa_ids),'products':len(qa_products),'text_keys':len(qa_keys)})
    args.output_dir.mkdir(parents=True)
    args.clusters_output.parent.mkdir(parents=True,exist_ok=True)
    write_csv(args.clusters_output, ['normalization','text_sha256','rows','cross_product',
              'mixed_ratings','different_text_variants'], clusters)
    (args.output_dir/'audit.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in {'word_length_distribution','observed_types','qa_sources'}},indent=2))


if __name__ == '__main__':
    main()
