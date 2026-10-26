"""Fine-tune ASC unweighted/balanced trên gold aspects; lock validation trước official test."""
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
os.environ.setdefault('HF_HUB_DISABLE_PROGRESS_BARS','1')

import numpy as np
import psutil
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader
from transformers import BertConfig,BertForSequenceClassification,get_linear_schedule_with_warmup
from huggingface_hub import hf_hub_download

from src.absa.sentiment import AspectSentimentDataset,evaluate_asc
from src.absa.sentiment_data import MARKERS,load_asc_records,load_p9_config
from src.config import PROJECT_ROOT
from src.evaluation.classification import LABELS,ResourceMonitor
from src.evaluation.error_diagnosis import file_hash
from src.sentiment.bert import LengthBatchSampler,collate_tokens,resolve_device,seed_everything


def write_json(path: Path,value) -> None:
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def save_asc_model(model,directory: Path,cfg: dict,tokenizer: Path) -> None:
    directory.mkdir(parents=True,exist_ok=True); model.save_pretrained(directory,safe_serialization=True)
    shutil.copy2(tokenizer,directory/'tokenizer.json')
    write_json(directory/'asc_metadata.json',{'labels':list(LABELS),'label_to_id':{l:i for i,l in enumerate(LABELS)},
               'max_length':cfg['max_length'],'markers':list(MARKERS),'representation':cfg['representation'],
               'tokenizer_sha256':file_hash(tokenizer),'conflict_policy':cfg['conflict_policy'],
               'domain':'laptop','language':'en','confidence':'null_uncalibrated'})


def run(*,resume: bool=False,root: Path=PROJECT_ROOT) -> dict:
    cfg=load_p9_config(root/'configs/p9_aspect_sentiment.yaml'); tc=cfg['training']
    report=root/cfg['report_directory']; out=root/cfg['model_directory']; local=root/cfg['prediction_directory']
    data=root/cfg['data_directory']; manifest_path=data/'manifest.json'
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    if manifest['config']!=cfg or manifest['status']!='PASS': raise ValueError('ASC data/config chưa PASS')
    if (report/'selection_lock.json').exists() or (report/'result.json').exists():
        raise ValueError('Không mở lại ASC experiment đã selection/test')
    if out.exists() and not resume: raise ValueError('Không ghi đè P9; chỉ --resume run chưa selection')
    if not out.exists() and resume: raise ValueError('Không có run ASC để resume')
    out.mkdir(parents=True,exist_ok=True); report.mkdir(parents=True,exist_ok=True); local.mkdir(parents=True,exist_ok=True)
    torch.set_num_threads(tc['threads']); device=resolve_device(tc['device']); amp=tc['mixed_precision']=='fp16' and device.type=='cuda'
    source=Path(hf_hub_download(cfg['pretrained_model'],'model.safetensors',revision=cfg['revision'],local_files_only=True))
    tokenizer=data/'tokenizer.json'
    paths=['scripts/train_p9.py','scripts/evaluate_p9_end_to_end.py','src/absa/sentiment.py','src/absa/sentiment_data.py',
           'src/evaluation/aspect_sentiment.py','src/inference/absa.py']
    identity={'config':cfg,'data_manifest_sha256':file_hash(manifest_path),'pretrained_sha256':file_hash(source),
              'tokenizer_sha256':file_hash(tokenizer),'source_sha256':{p:file_hash(root/p) for p in paths}}
    identity_path=report/'training_identity.json'
    if resume and json.loads(identity_path.read_text(encoding='utf-8'))!=identity: raise ValueError('ASC resume identity thay đổi')
    write_json(identity_path,identity)
    # Gold-aspect test không được mở trong training/model selection.
    train=load_asc_records(root,manifest,'train'); val=load_asc_records(root,manifest,'validation')
    dataset=AspectSentimentDataset(train,'train')
    candidates=[]; all_history=[]; started=time.perf_counter(); elapsed_before=0.
    if device.type=='cuda': torch.cuda.reset_peak_memory_stats()
    def guard():
        if elapsed_before+time.perf_counter()-started>tc['max_seconds']: raise RuntimeError('Vượt ngân sách P9')
        if psutil.Process().memory_info().rss>tc['max_process_rss_bytes']: raise RuntimeError('Vượt RSS P9')
    with ResourceMonitor() as monitor:
        for mode in tc['loss_candidates']:
            mode_out=out/mode; mode_out.mkdir(exist_ok=True)
            completed=report/f'{mode}_complete.json'
            if resume and completed.exists():
                candidate=json.loads(completed.read_text(encoding='utf-8'))
                if file_hash(mode_out/'best/model.safetensors')!=candidate['model_sha256']: raise ValueError('Completed candidate hash thay đổi')
                candidates.append(candidate); all_history.extend(json.loads((report/f'{mode}_history.json').read_text(encoding='utf-8')))
                elapsed_before+=candidate['wall_seconds']; continue
            seed_everything(cfg['seed'])
            mc=BertConfig.from_pretrained(source.parent,local_files_only=True)
            mc.num_labels=3; mc.label2id={l:i for i,l in enumerate(LABELS)}; mc.id2label=dict(enumerate(LABELS))
            state_path=mode_out/'training_state.pt'; resume_mode=resume and state_path.exists()
            model=BertForSequenceClassification.from_pretrained(mode_out/'last' if resume_mode else source.parent,
                  config=mc,local_files_only=True,attn_implementation='sdpa').to(device)
            if tc['gradient_checkpointing']: model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False})
            sampler=LengthBatchSampler(dataset,tc['batch_size'],cfg['seed'])
            loader=DataLoader(dataset,batch_sampler=sampler,collate_fn=collate_tokens)
            optimizer=torch.optim.AdamW(model.parameters(),lr=tc['learning_rate'],weight_decay=tc['weight_decay'])
            steps=math.ceil(len(loader)/tc['gradient_accumulation'])*tc['epochs']
            scheduler=get_linear_schedule_with_warmup(optimizer,math.ceil(steps*tc['warmup_ratio']),steps)
            scaler=torch.amp.GradScaler('cuda',enabled=amp)
            weights=torch.tensor([manifest['balanced_weights_train_only'][l] for l in LABELS],device=device) if mode=='balanced' else None
            history=[]; best=-1.; best_epoch=None; start_epoch=0; mode_elapsed=0.
            if resume_mode:
                state=torch.load(state_path,map_location=device,weights_only=False)
                optimizer.load_state_dict(state['optimizer']); scheduler.load_state_dict(state['scheduler']); scaler.load_state_dict(state['scaler'])
                history=state['history']; best=state['best']; best_epoch=state['best_epoch']; start_epoch=state['next_epoch']; mode_elapsed=state['mode_wall_seconds']
                random.setstate(state['random_state']); np.random.set_state(state['numpy_state']); torch.set_rng_state(state['torch_state'].cpu())
                if device.type=='cuda': torch.cuda.set_rng_state_all([s.cpu() for s in state['cuda_state']])
            mode_started=time.perf_counter()
            for epoch in range(start_epoch,tc['epochs']):
                tick=time.perf_counter(); sampler.epoch=epoch; model.train(); optimizer.zero_grad(set_to_none=True)
                losses=[]; seen=0
                for step,batch in enumerate(loader):
                    guard(); labels=batch.pop('labels').to(device); seen+=len(labels)
                    group_size=min(tc['gradient_accumulation'],len(loader)-(step//tc['gradient_accumulation'])*tc['gradient_accumulation'])
                    with torch.autocast(device.type,dtype=torch.float16,enabled=amp):
                        logits=model(**{k:v.to(device) for k,v in batch.items()}).logits
                        loss=F.cross_entropy(logits,labels,weight=weights)
                    if not torch.isfinite(loss): raise ValueError('ASC loss không hữu hạn')
                    losses.append(float(loss.detach())); scaler.scale(loss/group_size).backward()
                    if (step+1)%tc['gradient_accumulation']==0 or step+1==len(loader):
                        scaler.unscale_(optimizer); torch.nn.utils.clip_grad_norm_(model.parameters(),tc['max_grad_norm'])
                        scale=scaler.get_scale(); scaler.step(optimizer); scaler.update()
                        if scaler.get_scale()>=scale: scheduler.step()
                        optimizer.zero_grad(set_to_none=True)
                    if (step+1)%100==0:
                        progress={'mode':mode,'epoch':epoch+1,'batch':step+1,'batches':len(loader),'seen':seen,'seconds':time.perf_counter()-tick}
                        write_json(report/'progress.json',progress); print(json.dumps(progress),flush=True)
                if seen!=len(train): raise ValueError('Không train đủ ASC examples')
                train_seconds=time.perf_counter()-tick; v_tick=time.perf_counter()
                score,pred=evaluate_asc(model,val,device,batch_size=tc['eval_batch_size'],amp=amp)
                history.append({'mode':mode,'epoch':epoch+1,'train_examples':seen,'mean_batch_loss':float(np.mean(losses)),
                   'validation':score,'training_seconds':train_seconds,'validation_seconds':time.perf_counter()-v_tick,
                   'class_weights':weights.tolist() if weights is not None else None})
                write_json(report/f'{mode}_history.json',history)
                if score['macro_f1']>best:
                    best=score['macro_f1']; best_epoch=epoch+1
                    save_asc_model(model,mode_out/'best',cfg,tokenizer)
                    write_json(local/f'{mode}_validation_predictions.json',pred)
                save_asc_model(model,mode_out/'last',cfg,tokenizer)
                torch.save({'next_epoch':epoch+1,'optimizer':optimizer.state_dict(),'scheduler':scheduler.state_dict(),
                    'scaler':scaler.state_dict(),'history':history,'best':best,'best_epoch':best_epoch,
                    'mode_wall_seconds':mode_elapsed+time.perf_counter()-mode_started,
                    'random_state':random.getstate(),'numpy_state':np.random.get_state(),'torch_state':torch.get_rng_state(),
                    'cuda_state':torch.cuda.get_rng_state_all() if device.type=='cuda' else []},state_path)
                print(json.dumps({'mode':mode,'epoch':epoch+1,'validation_macro_f1':score['macro_f1']}),flush=True)
            candidate={'mode':mode,'epoch':best_epoch,'validation_macro_f1':best,
                       'model_sha256':file_hash(mode_out/'best/model.safetensors'),
                       'wall_seconds':mode_elapsed+time.perf_counter()-mode_started}
            write_json(completed,candidate); candidates.append(candidate); all_history.extend(history)
            del model,optimizer,scheduler,scaler,weights; gc.collect()
            if device.type=='cuda': torch.cuda.empty_cache()
        write_json(report/'history.json',all_history)
        selected=max(candidates,key=lambda r:r['validation_macro_f1']); mode=selected['mode']; chosen=out/mode/'best'
        lock={'selected':selected,'candidates':candidates,'selection_metric':'validation_macro_f1',
              'tie_break':tc['tie_break'],'selection_complete_before_test':True,'test_used_for_selection':False,
              'data_manifest_sha256':file_hash(manifest_path),'training_identity_sha256':file_hash(identity_path),
              'history_sha256':file_hash(report/'history.json')}
        write_json(report/'selection_lock.json',lock); lock_sha=file_hash(report/'selection_lock.json')
        model=BertForSequenceClassification.from_pretrained(chosen,local_files_only=True).to(device)
        v_tick=time.perf_counter(); val_metrics,reloaded=evaluate_asc(model,val,device,batch_size=tc['eval_batch_size'],amp=amp)
        if reloaded!=json.loads((local/f'{mode}_validation_predictions.json').read_text(encoding='utf-8')):
            raise ValueError('ASC reload không tái lập validation predictions')
        val_seconds=time.perf_counter()-v_tick
        test=load_asc_records(root,manifest,'test'); t_tick=time.perf_counter()
        test_metrics,test_predictions=evaluate_asc(model,test,device,batch_size=tc['eval_batch_size'],amp=amp)
        test_seconds=time.perf_counter()-t_tick
        for split,metrics,pred in [('validation',val_metrics,reloaded),('test',test_metrics,test_predictions)]:
            write_json(report/f'{split}_metrics.json',metrics)
            (local/f'{split}_predictions.jsonl').write_text(''.join(json.dumps(p,ensure_ascii=False)+'\n' for p in pred),encoding='utf-8')
        if file_hash(report/'selection_lock.json')!=lock_sha: raise ValueError('ASC selection lock thay đổi')
        result={'status':'STANDALONE_ASC_COMPLETE','selected':selected,'validation':val_metrics,'test':test_metrics,
                'model_directory':chosen.relative_to(root).as_posix(),'selection_lock_sha256':lock_sha,
                'reload_validation_predictions_identical':True,'test_prediction_passes':1,'test_tuning':False,
                'training_seconds':sum(r['training_seconds'] for r in all_history),'validation_seconds':val_seconds,'test_seconds':test_seconds,
                'inference_ms_per_gold_aspect_from_tokens':test_seconds/len(test)*1000,
                'runtime_seconds_including_checkpoint_io':elapsed_before+time.perf_counter()-started,
                'peak_process_rss_bytes_current_process':monitor.peak_rss_bytes,
                'peak_gpu_allocated_bytes':torch.cuda.max_memory_allocated() if device.type=='cuda' else None,
                'peak_gpu_reserved_bytes':torch.cuda.max_memory_reserved() if device.type=='cuda' else None,
                'artifact_bytes':sum(p.stat().st_size for p in chosen.iterdir() if p.is_file()),
                'gpu_name':torch.cuda.get_device_name() if device.type=='cuda' else None,
                'versions':{'python':__import__('sys').version.split()[0],'torch':torch.__version__,
                            'transformers':__import__('transformers').__version__}}
        write_json(report/'result.json',result)
    return result


if __name__=='__main__':
    if hasattr(__import__('sys').stdout,'reconfigure'): __import__('sys').stdout.reconfigure(encoding='utf-8')
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--resume',action='store_true');a=p.parse_args()
    result=run(resume=a.resume);print(json.dumps(result),flush=True)
