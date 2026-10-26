"""Xác minh bằng chứng QA của đã cố định và sao chép ước tính v2 thành bản tóm tắt mới."""

import argparse
import json
from pathlib import Path

from src.config import load_config
from src.data.acquisition import sha256_file
from src.data.independent_qa import read_csv
from src.data.laptop_filter import classify_product
from src.data.supplemental_qa import evaluate_supplemental_qa
from src.data.validation import stable_key
from src.evaluation.sampling_uncertainty import review_estimates


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evaluation-dir',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    if args.output_dir.exists():
        parser.error('Use a new output directory')
    current=json.loads((args.evaluation_dir/'evaluation.json').read_text(encoding='utf-8'))
    binding=current['normalization_binding']
    kit=Path(binding['source']).parent
    reproduced=evaluate_supplemental_qa(kit,annotator=current['annotator'],confirm_human=True,
        ai_assisted_review=current['ai_assistance'],review_annotations=Path(binding['path']),
        review_confirmation=Path(binding['confirmation_path']))
    if reproduced!=current:
        raise ValueError('Saved evaluation differs from reproduced result')
    manifest=json.loads((kit/'manifest.json').read_text(encoding='utf-8'))
    rules=load_config('acquisition')['filter']
    if stable_key(rules,0)!=manifest['rules_sha256']:
        raise ValueError('Rules differ from frozen sampling snapshot')
    old=json.loads(Path(manifest['pilot_evaluation']).read_text(encoding='utf-8'))
    keep, reject=(old['strata']['review:'+name] for name in ('random_keep','random_reject'))
    pilot=review_estimates(keep['frame_population'],keep['sample_size'],keep['counts']['TP'],
        reject['frame_population'],reject['sample_size'],reject['counts']['FN'])
    prior=json.loads(Path('reports/tables/p1_recall_reliability.json').read_text(encoding='utf-8'))
    if pilot!=prior['estimates']:
        raise ValueError('Pilot formula/interval reproduction differs from frozen audit')
    _,new_rows=read_csv(Path(binding['path']))
    _,old_rows=read_csv(Path(manifest['pilot_kit'])/'review_annotation.csv')
    if {r['review_id'] for r in new_rows}&{r['review_id'] for r in old_rows}:
        raise ValueError('Review sampling units overlap')
    errors=[]
    metadata={}
    for task in ('product','review'):
        _,rows=read_csv(Path(manifest['pilot_kit'])/f'{task}_annotation.csv')
        metadata.update({r['annotation_id']:r for r in rows})
    for row in old['comparisons']:
        if row['outcome']=='FN':
            source=metadata[row['annotation_id']]
            errors.append({'round':'v1','task':row['task'],'stratum':row['stratum'],
                'product_id':row['product_id'],'title':source['title'],
                'categories':json.loads(source['categories']),'pipeline_reason':row['pipeline_reason'],
                'human_error_reason':source['human_error_reason'],'human_notes':source['human_notes']})
    for row in new_rows:
        if row['human_label']=='laptop':
            decision=classify_product({'parent_asin':row['product_id'],'title':row['title'],
                                      'categories':json.loads(row['categories'])},rules)
            if decision.include:
                raise ValueError('FN metadata now contradicts frozen rule')
            errors.append({'round':'v2','task':'review','stratum':'random_reject_complement',
                'product_id':row['product_id'],'title':row['title'],
                'categories':json.loads(row['categories']),'pipeline_reason':decision.reason,
                'human_error_reason':row['human_error_reason'],'human_notes':row['human_notes']})
    protected=json.loads(Path('reports/tables/p1_recall_brand_preservation.json').read_text(encoding='utf-8'))['files']
    preservation={p:sha256_file(Path(p))==h for p,h in protected.items()}
    if not all(preservation.values()):
        raise ValueError('Protected files changed')
    result={'reproduction':'PASS','v1_estimates':pilot,'combined_estimates':current['combined_weighted_estimates'],
        'supplemental_counts':current['counts'], 'review_overlap':False,
        'diagnostic_rows_excluded':True,'pilot_reject_as_certainty':True,
        'annotation_provenance':current['annotation_process'],'errors':errors,
        'protected_unchanged':len(preservation),'preservation':preservation,
        'source_hashes':{p:sha256_file(Path(p)) for p in [binding['source'],binding['path'],
            binding['confirmation_path'],'data/manual/laptop_filter_qa.csv',
            'data/manual/feasibility/Electronics_laptop_3aeb96dfe815.csv']},
        'acceptance':'NEEDS REVIEW; no new recall/F1/brand threshold'}
    args.output_dir.mkdir(parents=True)
    (args.output_dir/'summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'reproduction':'PASS','protected_files':len(preservation),'fn_examples':len(errors)},indent=2))


if __name__=='__main__':
    main()
