"""Joint ABSA sau standalone lock: dùng P8 spans đã lưu, không rerun hoặc retrain P8."""
import json
from pathlib import Path
import time

import torch
from transformers import AutoModelForSequenceClassification,AutoTokenizer,BertForSequenceClassification

from src.absa.extraction_data import load_records as load_p8_records
from src.absa.sentiment import predict_asc
from src.absa.sentiment_data import asc_tokenizer,encode_aspect,load_p9_config
from src.config import PROJECT_ROOT
from src.evaluation.aspect_sentiment import joint_metrics
from src.evaluation.error_diagnosis import file_hash
from src.sentiment.bert import resolve_device


def build_end_to_end_inputs(rows: list[dict],p8_predictions: list[dict],tokenizer,max_length: int,*,encoder=encode_aspect) -> tuple[list,list]:
    """Không dùng gold aspect/polarity để tạo classifier inputs của end-to-end."""
    if [r['uid'] for r in rows]!=[r['uid'] for r in p8_predictions]: raise ValueError('P8 prediction UID/order không khớp')
    inputs=[]; mapping=[]
    for row,pred in zip(rows,p8_predictions):
        if row['text']!=pred['text']: raise ValueError('P8 prediction text không khớp')
        for index,aspect in enumerate(pred['predicted_aspects']):
            encoded=encoder(row['text'],aspect['term'],aspect['start'],aspect['end'],tokenizer,max_length)
            inputs.append({**encoded,'example_id':f"e2e:{row['uid']}:{index}",'split':row['split'],'label_id':None})
            mapping.append((row['uid'],aspect))
    return inputs,mapping


def evaluate_end_to_end(root: Path=PROJECT_ROOT,*,config_path: Path | None=None) -> dict:
    cfg=load_p9_config(config_path or root/'configs/p9_aspect_sentiment.yaml')
    if not cfg['end_to_end']['enabled'] or cfg['end_to_end']['conflict_policy']!='exclude_gold_and_ignore_exact_conflict_predictions':
        raise ValueError('End-to-end policy chưa được hỗ trợ')
    report=root/cfg['report_directory']; local=root/cfg['prediction_directory']; output=report/'end_to_end_results.json'
    if output.exists(): raise ValueError('Không mở lại end-to-end run đã đánh giá; chỉ tính lại saved predictions')
    result=json.loads((report/'result.json').read_text(encoding='utf-8'))
    lock=json.loads((report/'selection_lock.json').read_text(encoding='utf-8'))
    if result['status']!='STANDALONE_ASC_COMPLETE' or file_hash(report/'selection_lock.json')!=result['selection_lock_sha256']:
        raise ValueError('Standalone ASC chưa hoàn tất và khóa')
    chosen=root/result['model_directory']
    if file_hash(chosen/'model.safetensors')!=lock['selected']['model_sha256']: raise ValueError('ASC checkpoint hash thay đổi')
    p8=json.loads((root/cfg['p8_manifest']).read_text(encoding='utf-8'))
    p8_verified=json.loads((root/'reports/p8_20261026/independent_evaluation.json').read_text(encoding='utf-8'))
    torch.set_num_threads(cfg['training']['threads']); device=resolve_device(cfg['training']['device'])
    encoder=encode_aspect
    if cfg.get('experiment'):
        from src.absa.sentiment_backbone import encode_record
        tokenizer=AutoTokenizer.from_pretrained(chosen,local_files_only=True)
        def encoder(text,aspect,start,end,tokenizer,max_length):
            return encode_record({'text':text,'aspect':aspect,'start':start,'end':end},tokenizer,max_length)
        model=AutoModelForSequenceClassification.from_pretrained(chosen,local_files_only=True).to(device)
    else:
        tokenizer=asc_tokenizer(chosen/'tokenizer.json')
        model=BertForSequenceClassification.from_pretrained(chosen,local_files_only=True).to(device)
    summary={'status':'COMPLETE','source':'frozen P8 saved predictions -> locked P9 classifier',
             'p8_inference_rerun':False,'asc_selection_lock_sha256':file_hash(report/'selection_lock.json'),
             'protocol':'P8 predicted spans only; conflict handling evaluation-only after inference',
             'splits':{}}
    for split in ['validation','test']:
        rows=load_p8_records(root,p8,split); path=root/cfg['p8_predictions']/f'{split}_predictions.jsonl'
        if file_hash(path)!=p8_verified['prediction_sha256'][split]: raise ValueError('Frozen P8 predictions hash thay đổi')
        p8_pred=[json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
        inputs,mapping=build_end_to_end_inputs(rows,p8_pred,tokenizer,cfg['max_length'],encoder=encoder)
        tick=time.perf_counter()
        labels=predict_asc(model,inputs,device,batch_size=cfg['training']['eval_batch_size'],amp=device.type=='cuda')
        seconds=time.perf_counter()-tick
        by_uid={r['uid']:{'uid':r['uid'],'sentence_id':r['sentence_id'],'text':r['text'],
                  'gold_aspects':[{**a,'polarity':r['aspects'][a['original_aspect_index']]['polarity']} for a in r['extraction_aspects']],
                  'predicted_aspects':[]} for r in rows}
        for (uid,aspect),label in zip(mapping,labels):
            by_uid[uid]['predicted_aspects'].append({'term':aspect['term'],'start':aspect['start'],'end':aspect['end'],
                       'sentiment':cfg['labels'][label],'aspect_score':None,'sentiment_score':None})
        predictions=list(by_uid.values()); metrics=joint_metrics(predictions)
        (local/f'{split}_end_to_end_predictions.jsonl').write_text(''.join(json.dumps(p,ensure_ascii=False)+'\n' for p in predictions),encoding='utf-8')
        (local/f'{split}_end_to_end_decomposition.json').write_text(json.dumps(metrics['decomposition'],ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        metrics.pop('decomposition')
        summary['splits'][split]={'metrics':metrics,'asc_seconds_from_p8_spans':seconds,'p8_prediction_sha256':file_hash(path),
                'prediction_sha256':file_hash(local/f'{split}_end_to_end_predictions.jsonl'),'classifier_examples':len(inputs)}
    output.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return summary


if __name__=='__main__':
    result=evaluate_end_to_end();print(json.dumps(result))
