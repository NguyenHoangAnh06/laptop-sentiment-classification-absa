"""Fine-tune duy nhất BERT ATE; chọn validation entity F1 rồi mở official test một lần."""
import argparse
import gc
import json
import math
import os
from pathlib import Path
import random
import shutil
import time

os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG',':4096:8')
os.environ.setdefault('TOKENIZERS_PARALLELISM','false')

import numpy as np
import psutil
import torch
from torch.utils.data import DataLoader
from transformers import BertConfig, BertForTokenClassification, get_linear_schedule_with_warmup
from huggingface_hub import hf_hub_download

from src.absa.extraction import AspectDataset,collate_ate,evaluate_ate
from src.absa.extraction_data import LABELS,load_p8_config,load_records
from src.config import PROJECT_ROOT
from src.evaluation.classification import ResourceMonitor
from src.evaluation.error_diagnosis import file_hash
from src.sentiment.bert import LengthBatchSampler,resolve_device,seed_everything


def write_json(path: Path, value: dict | list) -> None:
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def save_model(model, directory: Path, cfg: dict, tokenizer: Path) -> None:
    directory.mkdir(parents=True,exist_ok=True)
    model.save_pretrained(directory,safe_serialization=True)
    shutil.copy2(tokenizer,directory/'tokenizer.json')
    write_json(directory/'extraction_metadata.json',{'labels':list(LABELS),'max_length':cfg['max_length'],
               'subword_policy':cfg['subword_policy'],'span_policy':cfg['span_policy'],
               'decode_policy':cfg['decode_policy'],'tokenizer_sha256':file_hash(tokenizer),
               'domain':'laptop','language':'en','confidence':'null_uncalibrated'})


def run(*, resume: bool=False, root: Path=PROJECT_ROOT) -> dict:
    cfg=load_p8_config(root/'configs/p8_aspect_extraction.yaml'); train_cfg=cfg['training']
    report=root/cfg['report_directory']; out=root/cfg['model_directory']
    data_dir=root/cfg['data_directory']; prediction_dir=root/cfg['prediction_directory']
    data_manifest=data_dir/'manifest.json'
    manifest=json.loads(data_manifest.read_text(encoding='utf-8'))
    if manifest['config']!=cfg or manifest['alignment']['unexplained_failures']:
        raise ValueError('BIO data/config chưa được xác minh')
    if (report/'selection_lock.json').exists() or (report/'result.json').exists():
        raise ValueError('Không mở lại experiment đã selection/test; dùng namespace mới có thiết kế độc lập')
    if out.exists() and not resume: raise ValueError('Không ghi đè model P8; dùng --resume cho run chưa selection')
    if not out.exists() and resume: raise ValueError('Không có checkpoint để resume')
    report.mkdir(parents=True,exist_ok=True); out.mkdir(parents=True,exist_ok=True)
    prediction_dir.mkdir(parents=True,exist_ok=True)
    device=resolve_device(train_cfg['device'])
    amp=train_cfg['mixed_precision']=='fp16' and device.type=='cuda'
    torch.set_num_threads(train_cfg['threads']); seed_everything(cfg['seed'])
    source=Path(hf_hub_download(cfg['pretrained_model'],'model.safetensors',revision=cfg['revision'],local_files_only=True))
    tokenizer=root/cfg['tokenizer']
    identity={'data_manifest_sha256':file_hash(data_manifest),'config':cfg,
              'pretrained_sha256':file_hash(source),'tokenizer_sha256':file_hash(tokenizer),
              'source_sha256':{p:file_hash(root/p) for p in ['scripts/train_p8.py','src/absa/extraction.py',
                              'src/absa/extraction_data.py','src/evaluation/aspect_extraction.py']}}
    identity_path=report/'training_identity.json'
    if resume and json.loads(identity_path.read_text(encoding='utf-8'))!=identity:
        raise ValueError('Resume identity/config/data/source không khớp')
    write_json(identity_path,identity)
    # Không load test records trong training/model selection.
    train=load_records(root,manifest,'train'); validation=load_records(root,manifest,'validation')
    dataset=AspectDataset(train,'train')
    sampler=LengthBatchSampler(dataset,train_cfg['batch_size'],cfg['seed'])
    loader=DataLoader(dataset,batch_sampler=sampler,collate_fn=collate_ate)
    model_cfg=BertConfig.from_pretrained(source.parent,local_files_only=True)
    model_cfg.num_labels=3; model_cfg.id2label=dict(enumerate(LABELS)); model_cfg.label2id={l:i for i,l in enumerate(LABELS)}
    model=BertForTokenClassification.from_pretrained(out/'last' if resume else source.parent,
        config=model_cfg,local_files_only=True,attn_implementation='sdpa').to(device)
    if train_cfg['gradient_checkpointing']:
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False})
    optimizer=torch.optim.AdamW(model.parameters(),lr=train_cfg['learning_rate'],weight_decay=train_cfg['weight_decay'])
    steps=math.ceil(len(loader)/train_cfg['gradient_accumulation'])*train_cfg['epochs']
    scheduler=get_linear_schedule_with_warmup(optimizer,math.ceil(steps*train_cfg['warmup_ratio']),steps)
    scaler=torch.amp.GradScaler('cuda',enabled=amp)
    history=[]; best=-1.; best_epoch=None; start_epoch=0; elapsed_before=0.
    if resume:
        state=torch.load(out/'training_state.pt',map_location=device,weights_only=False)
        optimizer.load_state_dict(state['optimizer']); scheduler.load_state_dict(state['scheduler']); scaler.load_state_dict(state['scaler'])
        history=state['history']; best=state['best']; best_epoch=state['best_epoch']; start_epoch=state['next_epoch']; elapsed_before=state['elapsed_seconds']
        random.setstate(state['random_state']); np.random.set_state(state['numpy_state']); torch.set_rng_state(state['torch_state'].cpu())
        if device.type=='cuda': torch.cuda.set_rng_state_all([s.cpu() for s in state['cuda_state']])
    if device.type=='cuda': torch.cuda.reset_peak_memory_stats()
    started=time.perf_counter()
    def guard():
        if time.perf_counter()-started+elapsed_before>train_cfg['max_seconds']: raise RuntimeError('Vượt ngân sách thời gian P8')
        if psutil.Process().memory_info().rss>train_cfg['max_process_rss_bytes']: raise RuntimeError('Vượt ngân sách RSS P8')
    with ResourceMonitor() as monitor:
        for epoch in range(start_epoch,train_cfg['epochs']):
            tick=time.perf_counter(); sampler.epoch=epoch; model.train(); optimizer.zero_grad(set_to_none=True)
            losses=[]; seen=0
            for step,batch in enumerate(loader):
                guard(); seen+=len(batch['input_ids'])
                group_size=min(train_cfg['gradient_accumulation'],len(loader)-(step//train_cfg['gradient_accumulation'])*train_cfg['gradient_accumulation'])
                with torch.autocast(device.type,dtype=torch.float16,enabled=amp):
                    loss=model(**{k:v.to(device) for k,v in batch.items()}).loss
                if not torch.isfinite(loss): raise ValueError('Loss ATE không hữu hạn')
                losses.append(float(loss.detach())); scaler.scale(loss/group_size).backward()
                if (step+1)%train_cfg['gradient_accumulation']==0 or step+1==len(loader):
                    scaler.unscale_(optimizer); torch.nn.utils.clip_grad_norm_(model.parameters(),train_cfg['max_grad_norm'])
                    scale=scaler.get_scale(); scaler.step(optimizer); scaler.update()
                    if scaler.get_scale()>=scale: scheduler.step()
                    optimizer.zero_grad(set_to_none=True)
                if (step+1)%100==0:
                    progress={'epoch':epoch+1,'batch':step+1,'batches':len(loader),'seen':seen,'seconds':time.perf_counter()-tick}
                    write_json(report/'progress.json',progress); print(json.dumps(progress),flush=True)
            if seen!=len(train): raise ValueError('Không train đủ sentence trong epoch')
            training_seconds=time.perf_counter()-tick
            val_tick=time.perf_counter()
            val,pred=evaluate_ate(model,validation,device,batch_size=train_cfg['eval_batch_size'],amp=amp)
            entry={'epoch':epoch+1,'train_sentences':seen,'mean_batch_loss':float(np.mean(losses)),
                   'validation':val,'seconds':time.perf_counter()-tick,'training_seconds':training_seconds,
                   'validation_seconds':time.perf_counter()-val_tick}
            history.append(entry); write_json(report/'history.json',history); print(json.dumps(entry),flush=True)
            if val['entity_f1']>best:
                best=val['entity_f1']; best_epoch=epoch+1
                save_model(model,out/'best',cfg,tokenizer)
                write_json(prediction_dir/'selected_validation_predictions.json',pred)
            save_model(model,out/'last',cfg,tokenizer)
            torch.save({'next_epoch':epoch+1,'optimizer':optimizer.state_dict(),'scheduler':scheduler.state_dict(),
                        'scaler':scaler.state_dict(),'history':history,'best':best,'best_epoch':best_epoch,
                        'elapsed_seconds':elapsed_before+time.perf_counter()-started,
                        'random_state':random.getstate(),'numpy_state':np.random.get_state(),
                        'torch_state':torch.get_rng_state(),'cuda_state':torch.cuda.get_rng_state_all() if device.type=='cuda' else []},out/'training_state.pt')
        lock={'selected_epoch':best_epoch,'selection_metric':'validation_entity_f1','selected_value':best,
              'test_used_for_selection':False,'selection_complete_before_test':True,'tie_break':'earliest_epoch',
              'model_sha256':file_hash(out/'best/model.safetensors'),'training_identity_sha256':file_hash(identity_path),
              'data_manifest_sha256':file_hash(data_manifest),'history_sha256':file_hash(report/'history.json')}
        write_json(report/'selection_lock.json',lock); lock_sha=file_hash(report/'selection_lock.json')
        del model,optimizer,scheduler,scaler; gc.collect()
        if device.type=='cuda': torch.cuda.empty_cache()
        model=BertForTokenClassification.from_pretrained(out/'best',local_files_only=True).to(device)
        tick=time.perf_counter()
        val,reloaded=evaluate_ate(model,validation,device,batch_size=train_cfg['eval_batch_size'],amp=amp)
        if reloaded!=json.loads((prediction_dir/'selected_validation_predictions.json').read_text(encoding='utf-8')):
            raise ValueError('Checkpoint reload không tái lập validation predictions')
        validation_seconds=time.perf_counter()-tick
        # Official test lần đầu được mở trong runner sau selection lock.
        test=load_records(root,manifest,'test'); tick=time.perf_counter()
        test_metrics,test_pred=evaluate_ate(model,test,device,batch_size=train_cfg['eval_batch_size'],amp=amp)
        test_seconds=time.perf_counter()-tick
        for split,metric,pred in [('validation',val,reloaded),('test',test_metrics,test_pred)]:
            write_json(report/f'{split}_metrics.json',metric)
            (prediction_dir/f'{split}_predictions.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in pred),encoding='utf-8')
        if file_hash(report/'selection_lock.json')!=lock_sha: raise ValueError('Selection lock thay đổi')
        result={'status':'TRAINING_AND_EVALUATION_COMPLETE','selected_epoch':best_epoch,'epochs_run':len(history),
                'validation':val,'test':test_metrics,'test_prediction_passes':1,'test_tuning':False,
                'reload_validation_predictions_identical':True,'selection_lock_sha256':lock_sha,
                'validation_seconds':validation_seconds,'test_seconds':test_seconds,
                'inference_ms_per_sentence_from_tokens':test_seconds/len(test)*1000,
                'model_directory':(out/'best').relative_to(root).as_posix(),
                'artifact_bytes':sum(p.stat().st_size for p in (out/'best').iterdir() if p.is_file()),
                'runtime_seconds_including_checkpoint_io':time.perf_counter()-started+elapsed_before,
                'training_seconds':sum(r['training_seconds'] for r in history),
                'peak_process_rss_bytes_current_process':monitor.peak_rss_bytes,
                'peak_gpu_allocated_bytes':torch.cuda.max_memory_allocated() if device.type=='cuda' else None,
                'peak_gpu_reserved_bytes':torch.cuda.max_memory_reserved() if device.type=='cuda' else None,
                'device':str(device),'gpu_name':torch.cuda.get_device_name() if device.type=='cuda' else None,
                'versions':{'python':__import__('sys').version.split()[0],'torch':torch.__version__,
                            'transformers':__import__('transformers').__version__}}
        write_json(report/'result.json',result)
    return result


if __name__=='__main__':
    if hasattr(__import__('sys').stdout,'reconfigure'): __import__('sys').stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--resume',action='store_true')
    args=parser.parse_args()
    try:
        result=run(resume=args.resume); print(json.dumps(result),flush=True)
    except Exception as exc:
        print(json.dumps({'status':'FAILED','error_type':type(exc).__name__,'error':str(exc)}),flush=True)
        raise
