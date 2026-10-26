"""Chỉ chạy sau con người gán nhãn và xác nhận rõ ràng của người đánh giá."""

import argparse
import json
from pathlib import Path
from src.data.independent_qa import write_csv
from src.data.supplemental_qa import evaluate_supplemental_qa


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kit-dir',type=Path,required=True)
    parser.add_argument('--annotator',required=True)
    parser.add_argument('--confirm-human-review',action='store_true')
    provenance=parser.add_mutually_exclusive_group()
    provenance.add_argument('--ai-assisted-review',action='store_true')
    provenance.add_argument('--ai-history-unspecified',action='store_true')
    parser.add_argument('--review-annotations',type=Path)
    parser.add_argument('--review-confirmation',type=Path)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    if args.output_dir.exists():
        parser.error('Use a new output directory')
    result=evaluate_supplemental_qa(args.kit_dir,annotator=args.annotator,
                                   confirm_human=args.confirm_human_review,
                                   ai_assisted_review=None if args.ai_history_unspecified else args.ai_assisted_review,
                                   review_annotations=args.review_annotations,review_confirmation=args.review_confirmation)
    args.output_dir.mkdir(parents=True)
    (args.output_dir/'evaluation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    rows=result['comparisons']
    write_csv(args.output_dir/'comparisons.csv',list(rows[0]),rows)
    write_csv(args.output_dir/'errors.csv',list(rows[0]),[r for r in rows if r['outcome']=='FN'])
    (args.output_dir/'report.md').write_text('# Supplemental REJECT Human QA\n\n'+
        f"Status: {result['status']}\n\nAnnotator: {result['annotator']}; provenance: {result['label_provenance']}\n\n"+
        'Combined estimates use pilot REJECT units as certainty observations and SRS weights on the remaining frame; no naive pooling.\n\n'+
        '```json\n'+json.dumps(result['combined_weighted_estimates'],indent=2)+'\n```\n\n'+
        result['limitations']+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='comparisons'},indent=2))


if __name__=='__main__':
    main()
