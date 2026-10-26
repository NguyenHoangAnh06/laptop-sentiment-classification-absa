"""P9-EXP01: đổi backbone, dùng nguyên dữ liệu và trainer/evaluator P9."""
import argparse
import json
from pathlib import Path
import shutil

import yaml
from transformers import AutoTokenizer
from huggingface_hub import hf_hub_download

from src.absa.sentiment_data import MARKERS,load_asc_records,load_p9_config,marked_input
from src.config import PROJECT_ROOT
from src.evaluation.error_diagnosis import file_hash
from src.absa.sentiment_backbone import encode_record

NAMESPACE='p9_exp01_deberta_20261026_v2'
REVISION='8ccc9b6f36199bec6961081d44eb72fb3f7353f3'


def prepare(root: Path=PROJECT_ROOT) -> dict:
    """Tạo cache token riêng từ đúng processed P9, không rebuild annotation/split."""
    cfg=load_p9_config(root/'configs/p9_aspect_sentiment.yaml')
    original=json.loads((root/cfg['data_directory']/'manifest.json').read_text(encoding='utf-8'))
    report=root/'reports'/NAMESPACE; report.mkdir(parents=True,exist_ok=True)
    snapshot=report/'preservation_before.json'
    if not snapshot.exists():
        frozen=json.loads((root/'reports/p9_preservation_before.json').read_text(encoding='utf-8'))
        for base in ['data/processed/p9_20261026','artifacts/models/p9_20261026',
                     'reports/p9_20261026','data/interim/p9_20261026']:
            frozen.update({p.relative_to(root).as_posix():file_hash(p) for p in (root/base).rglob('*') if p.is_file()})
        frozen['reports/p9_aspect_sentiment.md']=file_hash(root/'reports/p9_aspect_sentiment.md')
        snapshot.write_text(json.dumps(frozen,indent=2)+'\n',encoding='utf-8')
    tokenizer=AutoTokenizer.from_pretrained('microsoft/deberta-v3-base',revision=REVISION)
    tokenizer.add_special_tokens({'additional_special_tokens':list(MARKERS)})
    # Transformers5 chuyển spm.model thiếu post_processor; khôi phục CLS/SEP chuẩn backbone.
    from tokenizers.processors import TemplateProcessing
    tokenizer.backend_tokenizer.post_processor=TemplateProcessing(
        single='[CLS] $A [SEP]',pair='[CLS] $A [SEP] $B:1 [SEP]:1',
        special_tokens=[('[CLS]',tokenizer.cls_token_id),('[SEP]',tokenizer.sep_token_id)])
    if tokenizer.pad_token_id!=0: raise ValueError('P9 collator cần pad ID0')
    cfg.update(experiment='P9-EXP01',version='p9_exp01_v1',pretrained_model='microsoft/deberta-v3-base',
               revision=REVISION,tokenizer_revision=REVISION,pretrained_filename='pytorch_model.bin',
               tokenizer_source='microsoft/deberta-v3-base',
               attention_implementation='eager',data_directory=f'data/processed/{NAMESPACE}',
               model_directory=f'artifacts/models/{NAMESPACE}',report_directory=f'reports/{NAMESPACE}',
               prediction_directory=f'data/interim/{NAMESPACE}')
    # Giữ effective batch16; giảm physical batch cho backbone lớn hơn trên GPU6GB.
    cfg['training'].update(batch_size=4,gradient_accumulation=4,eval_batch_size=8)
    target=root/cfg['data_directory']; target.mkdir(parents=True,exist_ok=True)
    config_path=root/'configs/p9_exp01_deberta.yaml'
    payload=yaml.safe_dump(cfg,allow_unicode=True,sort_keys=False)
    if config_path.exists() and config_path.read_text(encoding='utf-8')!=payload:
        raise ValueError('Config experiment đã tồn tại khác; không ghi đè')
    config_path.write_text(payload,encoding='utf-8')
    tokenizer.save_pretrained(target)
    manifest={**original,'config':cfg,'files':{},'canonical_manifest_sha256':file_hash(root/'data/processed/p9_20261026/manifest.json'),
              'tokenizer_sha256':file_hash(target/'tokenizer.json'),'marker_ids':tokenizer.convert_tokens_to_ids(list(MARKERS)),
              'tokenizer_source_sha256':file_hash(Path(hf_hub_download(cfg['pretrained_model'],'spm.model',revision=REVISION,local_files_only=True))),
              'representation':'[CLS] context_before [unused0] target_occurrence [unused1] context_after [SEP]; native DeBERTa vocabulary128003',
              'token_lengths':{}}
    for split,count in [('train',1999),('validation',314),('test',638)]:
        rows=load_asc_records(root,original,split)
        if len(rows)!=count: raise ValueError('Count P9 frozen không khớp yêu cầu')
        encoded=[encode_record(r,tokenizer,cfg['max_length']) for r in rows]
        path=target/f'{split}.jsonl'
        content=''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in encoded)
        if path.exists() and path.read_text(encoding='utf-8')!=content: raise ValueError('Cache experiment đã thay đổi')
        path.write_text(content,encoding='utf-8')
        manifest['files'][split]={'path':path.relative_to(root).as_posix(),'sha256':file_hash(path)}
        manifest['token_lengths'][split]={'count':count,'max':max(len(r['input_ids']) for r in encoded),'truncated':0}
    (target/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (report/'data_validation.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    # Chỉ weights pretrained, không lấy datasets hoặc pipeline từ repo tham khảo.
    hf_hub_download(cfg['pretrained_model'],cfg['pretrained_filename'],revision=REVISION)
    return manifest


def stability(root: Path=PROJECT_ROOT) -> list[dict]:
    """Chỉ best loss/config seed42; thêm seed43/44, không đọc official test."""
    from scripts.train_p9 import run
    cfg=load_p9_config(root/'configs/p9_exp01_deberta.yaml')
    primary=root/cfg['report_directory']; lock=json.loads((primary/'selection_lock.json').read_text(encoding='utf-8'))
    original=json.loads((root/cfg['data_directory']/'manifest.json').read_text(encoding='utf-8'))
    baseline=json.loads((root/'reports/p9_20261026/result.json').read_text(encoding='utf-8'))
    if lock['selected']['validation_macro_f1']<=baseline['validation']['macro_f1']:
        raise ValueError('Không chạy stability khi primary không thắng validation')
    results=[]
    for seed in [43,44]:
        run_cfg=json.loads(json.dumps(cfg)); namespace=f'{NAMESPACE}_seed{seed}'
        run_cfg.update(seed=seed,experiment='P9-EXP01-STABILITY',validation_only=True,
                       data_directory=f'data/processed/{namespace}',model_directory=f'artifacts/models/{namespace}',
                       report_directory=f'reports/{namespace}',prediction_directory=f'data/interim/{namespace}',
                       primary_selection_lock_sha256=file_hash(primary/'selection_lock.json'))
        run_cfg['training']['loss_candidates']=[lock['selected']['mode']]
        data=root/run_cfg['data_directory']; data.mkdir(parents=True,exist_ok=True)
        for name in ['tokenizer.json','tokenizer_config.json']:
            shutil.copy2(root/cfg['data_directory']/name,data/name)
        # Chỉ manifest/config training khác; các files trỏ đúng cache token primary frozen.
        (data/'manifest.json').write_text(json.dumps({**original,'config':run_cfg},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        config_path=root/f'configs/{namespace}.yaml'
        config_path.write_text(yaml.safe_dump(run_cfg,allow_unicode=True,sort_keys=False),encoding='utf-8')
        report=root/run_cfg['report_directory']
        if (report/'result.json').exists():
            result=json.loads((report/'result.json').read_text(encoding='utf-8'))
            if result['status']!='VALIDATION_ONLY_COMPLETE' or result['test_opened']: raise ValueError('Stability state không hợp lệ')
        else:
            result=run(root=root,config_path=config_path)
        results.append(result)
    (primary/'stability.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return results


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['prepare','train','stability']); args=parser.parse_args()
    if args.action=='prepare':
        print(json.dumps(prepare()['token_lengths']),flush=True)
    elif args.action=='stability':
        print(json.dumps(stability()),flush=True)
    else:
        from scripts.train_p9 import run
        print(json.dumps(run(config_path=PROJECT_ROOT/'configs/p9_exp01_deberta.yaml')),flush=True)
