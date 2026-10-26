"""Tính toán lại các ước tính đã cố định v1 và các khoảng dân số hữu hạn được phân tầng chính xác."""
import argparse
import json
import math
from collections import Counter
from pathlib import Path
from src.data.supplemental_qa import frozen_pilot
from src.evaluation.sampling_uncertainty import review_estimates,reject_sample_options,success_total_interval


def main() -> None:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--kit-dir',type=Path,default=Path('data/manual/independent_qa/p1_v1'))
    p.add_argument('--evaluation',type=Path,default=Path('reports/independent_qa/p1_v1_evaluation/evaluation.json'))
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if args.output.exists():raise FileExistsError(args.output)
    manifest,e,_=frozen_pilot(args.kit_dir,args.evaluation)
    private=json.loads((args.kit_dir/'private_predictions.json').read_text(encoding='utf-8'))
    audited={}
    for name in ('random_keep','random_reject'):
        key=f'review:{name}';stratum=e['strata'][key]
        rows=[r for r in e['comparisons'] if r['task']=='review' and r['stratum']==name]
        counts=Counter(r['outcome'] for r in rows)
        refs=[r for r in private if r['task']=='review' and r['stratum']==name]
        n=stratum['sample_size'];N=stratum['frame_population']
        assert len(rows)==len(refs)==n and counts==Counter(stratum['counts'])
        assert all(r['frame_population']==N and r['sample_size']==n and math.isclose(r['inclusion_probability'],n/N) for r in refs)
        audited[key]={'N':N,'n':n,'probability':n/N,'weight':N/n,'counts':dict(counts)}
    keep=e['strata']['review:random_keep'];reject=e['strata']['review:random_reject']
    result=review_estimates(keep['frame_population'],keep['sample_size'],keep['counts'].get('TP',0),
                           reject['frame_population'],reject['sample_size'],reject['counts'].get('FN',0))
    old=e['review_weighted_estimates']
    assert all(math.isclose(result[k],old[k]) for k in ('precision','recall','f1'))
    assert all(math.isclose(result['confusion_matrix'][k],old['confusion_matrix'][k]) for k in old['confusion_matrix'])
    planning=reject_sample_options(reject['frame_population'],reject['sample_size'],reject['counts'].get('FN',0))
    low,high=success_total_interval(reject['counts'].get('FN',0),reject['sample_size'],reject['frame_population'])
    n=planning['chosen_additional'];N=reject['frame_population']
    planning['pilot_95_prevalence_interval']=[low/N,high/N]
    planning['detection_probability_at_pilot_interval_endpoints_binomial_approx']=[1-(1-low/N)**n,1-(1-high/N)**n]
    output={'status':'AUDIT_PASS','formula_or_weight_bug_found':False,'strata':audited,
            'estimates':result,'planning':planning,'scope':manifest['scope'],
            'excluded_selected_but_invalid':manifest['populations']['excluded_selected_but_invalid_reviews'],
            'label_provenance':e['label_provenance'],
            'warnings':['Intervals assume fixed correct human labels, valid SRS and frozen population. Do not cover AI anchoring.',
                        'Diagnostic/uncertain samples never treated as negative or pooled into representative estimates.',
                        'Nonparametric bootstrap is unreliable with one FN; zero-event replicates collapse recall to 1.',
                        'Sample-size planning uses uncertain pilot rate; selected nominal precision is a planning target, not approved acceptance.']}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':output['status'],'recall':result['recall'],'recall_interval':result['intervals']['recall'],'planned_new_reviews':n},indent=2))


if __name__=='__main__':
    main()
