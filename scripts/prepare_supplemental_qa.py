"""Chuẩn bị QA TỪ CHỐI bổ sung; không bao giờ điền con người nhãn hoặc chạy khảo sát."""

import argparse
import json
from pathlib import Path
from src.config import load_config
from src.data.acquisition import sha256_file
from src.data.supplemental_qa import prepare_supplemental_qa
from src.evaluation.sampling_uncertainty import reject_sample_options


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir',type=Path,default=Path('data/interim/feasibility/electronics_full_laptop_30k'))
    parser.add_argument('--raw-dir',type=Path,default=Path('data/raw/amazon'))
    parser.add_argument('--pilot-kit',type=Path,default=Path('data/manual/independent_qa/p1_v1'))
    parser.add_argument('--pilot-evaluation',type=Path,default=Path('reports/independent_qa/p1_v1_evaluation/evaluation.json'))
    parser.add_argument('--output-dir',type=Path,required=True)
    parser.add_argument('--seed',type=int,default=20261008)
    parser.add_argument('--sample-size',type=int)
    args=parser.parse_args()
    e=json.loads(args.pilot_evaluation.read_text(encoding='utf-8'))['strata']['review:random_reject']
    planning=reject_sample_options(e['frame_population'],e['sample_size'],e['counts'].get('FN',0))
    result=prepare_supplemental_qa(args.run_dir,args.raw_dir,args.pilot_kit,args.pilot_evaluation,
                                  args.output_dir,load_config('acquisition'),load_config('feasibility')['limits'],
                                  sample_size=args.sample_size if args.sample_size is not None else planning['chosen_additional'],seed=args.seed)
    (args.output_dir/'sample_size_planning.json').write_text(json.dumps(planning,indent=2)+'\n',encoding='utf-8')
    planning_path=args.output_dir/'sample_size_planning.json'
    result['files'][planning_path.name]={'sha256':sha256_file(planning_path),'bytes':planning_path.stat().st_size}
    (args.output_dir/'manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':result['status'],'n':result['sample_size'],'resources':result['resources']},indent=2))


if __name__=='__main__':
    main()
