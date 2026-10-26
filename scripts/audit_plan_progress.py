"""Xác minh bằng chứng lập kế hoạch mà không cần chạy lại các thử nghiệm dữ liệu hoặc QA đã hoàn thành."""

import argparse
import json
import re
from pathlib import Path

from src.data.acquisition import sha256_file


def audit_progress() -> dict:
    """Trả lại ảnh chụp nhanh bằng chứng xác định, không phải cơ quan tiến độ khác."""
    plans = {name: Path(name).read_text(encoding='utf-8')
             for name in ('PLAN_HUMAN.md', 'PLAN_AI.md')}
    phase_ids = {}
    for name, text in plans.items():
        pattern = r'^# \d+\. CHẶNG (\d+) ' if name == 'PLAN_HUMAN.md' else r'^# \d+\. PHASE P(\d+) '
        phase_ids[name] = [int(x) for x in re.findall(pattern, text, re.M)]
        if phase_ids[name] != list(range(14)):
            raise ValueError(f'{name}: expected original P0-P13 sequence')

    protected = json.loads(Path('reports/tables/p1_recall_brand_preservation.json')
                           .read_text(encoding='utf-8'))['files']
    preservation = {p: sha256_file(Path(p)) == digest for p, digest in protected.items()}
    if not all(preservation.values()):
        raise ValueError('Protected file checksum mismatch')

    quality_path = Path('reports/data_quality/candidate_pool_20261009/audit.json')
    quality = json.loads(quality_path.read_text(encoding='utf-8'))
    if sha256_file(Path(quality['source'])) != quality['source_sha256']:
        raise ValueError('Quality evidence no longer matches candidate source')
    source_report = Path(quality['source']).parent / 'report.json'
    if sha256_file(source_report) != quality['run_report_sha256']:
        raise ValueError('Quality evidence run-report binding changed')
    if sum(quality['rating_proxy_class_counts'].values()) != quality['rows']:
        raise ValueError('Proxy class denominator differs from candidate count')
    for path, digest in quality['qa_sources'].items():
        if sha256_file(Path(path)) != digest:
            raise ValueError(f'Quality QA binding changed: {path}')

    evaluation_path = Path('reports/independent_qa/p1_v2_evaluation_20261009/evaluation.json')
    evaluation = json.loads(evaluation_path.read_text(encoding='utf-8'))
    binding = evaluation['normalization_binding']
    # Bản tóm tắt hiện có lưu trữ các hàm băm gốc, chuẩn và sidecar đã được phê duyệt.
    summary_path = Path('reports/independent_qa/p1_v2_summary_20261009/summary.json')
    summary = json.loads(summary_path.read_text(encoding='utf-8'))
    for path, digest in summary['source_hashes'].items():
        if sha256_file(Path(path)) != digest:
            raise ValueError(f'Approved annotation binding changed: {path}')
    if evaluation['annotation_sha256'] != sha256_file(Path(binding['path'])):
        raise ValueError('Evaluation annotation binding changed')
    if evaluation['combined_weighted_estimates'] != summary['combined_estimates']:
        raise ValueError('Saved QA estimates disagree')

    paths = {Path('AGENTS.md'), Path('PLAN_HUMAN.md'), Path('PLAN_AI.md'),
             Path('README.md'), Path('data_dictionary.md'),
             Path('customer_sentiment_analysis_plan.docx'), Path('docs/CODEX_HANDOFF.md')}
    paths.update(Path('docs').glob('*.md'))
    paths.update(Path('reports').glob('*.md'))
    paths.update(Path('reports/archive/p1_legacy_workflow').glob('*.md'))
    paths.update((quality_path, evaluation_path, summary_path, Path('scripts/audit_plan_progress.py')))
    return {
        'purpose': 'Evidence snapshot subordinate to PLAN_HUMAN and PLAN_AI; no independent roadmap',
        'phase_sequence': phase_ids, 'protected_files': len(preservation),
        'protected_checksums': preservation, 'evidence_bindings': 'PASS',
        'candidate_rows': quality['rows'], 'missing_by_field': quality['missing_by_field'],
        'duplicate_excess': {'exact': quality['raw_exact_duplicates']['duplicate_excess_rows'],
                             'normalized': quality['normalized_duplicates']['duplicate_excess_rows']},
        'proxy_counts': quality['rating_proxy_class_counts'],
        'qa_counts': evaluation['counts'],
        'combined_estimates': evaluation['combined_weighted_estimates'],
        'clean_dataset_exists': Path('data/processed/laptop_reviews.parquet').exists(),
        'gold_dataset_exists': Path('data/manual/amazon_laptop_gold_test.csv').exists(),
        'streamlit_entrypoint_exists': Path('app/streamlit_app.py').exists(),
        'document_sha256': {p.as_posix(): sha256_file(p) for p in sorted(paths)},
        'limits': 'Saved statistics verified against source hashes; no reannotation, cleaning, '
                  'full-survey rerun, new independence acceptance or licence verification.'}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Use a new output path')
    if Path('reports').resolve() not in args.output.resolve().parents:
        parser.error('Output must be under reports')
    result = audit_progress()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'protected_files': result['protected_files'],
                      'evidence_bindings': result['evidence_bindings'],
                      'phase_sequence': 'P0-P13 unchanged'}, indent=2))


if __name__ == '__main__':
    main()
