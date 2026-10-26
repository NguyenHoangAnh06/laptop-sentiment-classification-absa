"""Fine-tune BERT canonical title+body, lựa chọn validation rồi mở test một lần."""

import gc
import json
import math
import os
from pathlib import Path
import time

os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG', ':4096:8')
os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')

import numpy as np
import pandas as pd
import psutil
import torch
from torch.utils.data import DataLoader
import yaml
from huggingface_hub import hf_hub_download
from transformers import BertConfig, BertForSequenceClassification, get_linear_schedule_with_warmup

from scripts.revalidate_model_data import write_json
from scripts.train_modern import ORDER, latest_report, metrics
from scripts.train_p6 import save_checkpoint, smoke_test
from src.config import PROJECT_ROOT
from src.data.acquisition import sha256_file
from src.evaluation.classification import LABELS, ResourceMonitor
from src.preprocessing.semantic_cache import load_cache, load_semantic_config
from src.sentiment.bert import (LABEL_TO_ID, P4BertDataset, LengthBatchSampler,
    class_weights, collate_tokens, evaluate, seed_everything)


def run():
    root = PROJECT_ROOT
    cfg = yaml.safe_load((root / 'configs/transformer_benchmark.yaml').read_text(encoding='utf-8'))
    semantic = load_semantic_config()
    report = root / semantic['reports'] / 'E05_transformer'
    out = root / semantic['experiments'] / 'E05_transformer'
    if report.exists() or out.exists():
        raise ValueError('Không ghi đè experiment Transformer đã có')
    for name in ORDER:
        previous = latest_report(root / semantic['reports'] / name)
        if json.loads((previous / 'result.json').read_text(encoding='utf-8'))['status'] != 'PASS':
            raise ValueError('P5 chưa được nghiệm thu')
        if not (previous / 'independent_validation.json').is_file():
            raise ValueError('P5 chưa được xác minh độc lập')
    data, metadata = load_cache(semantic)
    report.mkdir(parents=True)
    out.mkdir(parents=True)
    write_json(report / 'config.json', {**cfg, 'transformer': semantic['transformer'],
               'canonical_text': semantic['canonical_text'], 'cache_identity': metadata['identity']})
    started = time.perf_counter()
    torch.set_num_threads(cfg['threads'])
    device = torch.device(cfg['device'])
    torch.cuda.reset_peak_memory_stats()
    datasets = {}
    for split in ('train', 'validation', 'test'):
        tokens = pd.read_parquet(root / semantic['cache'] / f'{split}_transformer_tokens.parquet')
        if tokens.review_id.tolist() != data[split]['frame'].review_id.tolist():
            raise ValueError('Sai thứ tự token canonical')
        if tokens.label_id.tolist() != data[split]['y'].tolist():
            raise ValueError('Sai nhãn token canonical')
        datasets[split] = P4BertDataset(tokens.assign(split=split).to_dict('records'),
            split=split, max_length=semantic['transformer']['max_length'], vocab_size=30522)
    source = Path(hf_hub_download(semantic['transformer']['checkpoint'], 'model.safetensors',
                               revision=semantic['transformer']['revision'], local_files_only=True))
    write_json(report / 'pretrained_source.json', {**semantic['transformer'], 'sha256': sha256_file(source),
        'license': 'Apache-2.0; reuse checkpoint đã tải ở experiment legacy, không reuse trọng số fine-tune'})
    model_cfg = BertConfig.from_json_file(root / Path(semantic['transformer']['tokenizer']).with_name('config.json'))
    model_cfg.num_labels, model_cfg.label2id, model_cfg.id2label = 3, LABEL_TO_ID, dict(enumerate(LABELS))

    def fresh():
        seed_everything(cfg['seed'])
        model = BertForSequenceClassification.from_pretrained(source.parent, config=model_cfg,
                    local_files_only=True, attn_implementation='sdpa').to(device)
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant': False})
        return model

    def guard():
        if time.perf_counter() - started > cfg['max_seconds']:
            raise RuntimeError('Vượt ngân sách thời gian P6')
        if psutil.Process().memory_info().rss > cfg['max_process_rss_bytes']:
            raise RuntimeError('Vượt ngân sách RSS P6')

    val_loader = DataLoader(datasets['validation'], batch_size=cfg['eval_batch_size'], collate_fn=collate_tokens)
    history, candidates = [], []
    with ResourceMonitor() as monitor:
        model = fresh()
        write_json(report / 'smoke.json', smoke_test(model, datasets['train'], device, True))
        del model
        gc.collect()
        torch.cuda.empty_cache()
        for mode in cfg['loss_candidates']:
            model = fresh()
            weights = class_weights(datasets['train'], mode)
            weights = weights.to(device) if weights is not None else None
            sampler = LengthBatchSampler(datasets['train'], cfg['batch_size'], cfg['seed'])
            loader = DataLoader(datasets['train'], batch_sampler=sampler, collate_fn=collate_tokens)
            optimizer = torch.optim.AdamW(model.parameters(), lr=cfg['learning_rate'], weight_decay=cfg['weight_decay'])
            total_steps = math.ceil(len(loader) / cfg['gradient_accumulation']) * cfg['epochs']
            scheduler = get_linear_schedule_with_warmup(optimizer, math.ceil(total_steps * cfg['warmup_ratio']), total_steps)
            scaler = torch.amp.GradScaler('cuda')
            best, stale = -1., 0
            for epoch in range(cfg['epochs']):
                model.train()
                sampler.epoch = epoch
                optimizer.zero_grad(set_to_none=True)
                epoch_start = time.perf_counter()
                seen = 0
                for step, batch in enumerate(loader):
                    guard()
                    labels = batch.pop('labels').to(device)
                    inputs = {k: v.to(device) for k, v in batch.items()}
                    group_size = min(cfg['gradient_accumulation'], len(loader) - (step // cfg['gradient_accumulation']) * cfg['gradient_accumulation'])
                    from src.sentiment.bert import training_loss
                    with torch.autocast('cuda', dtype=torch.float16):
                        loss = training_loss(model(**inputs).logits, labels, weights)
                    if not torch.isfinite(loss):
                        raise ValueError('Loss không hữu hạn')
                    scaler.scale(loss / group_size).backward()
                    seen += len(labels)
                    if (step+1) % cfg['gradient_accumulation'] == 0 or step+1 == len(loader):
                        scaler.unscale_(optimizer)
                        torch.nn.utils.clip_grad_norm_(model.parameters(), cfg['max_grad_norm'])
                        old_scale = scaler.get_scale()
                        scaler.step(optimizer)
                        scaler.update()
                        if scaler.get_scale() >= old_scale:
                            scheduler.step()
                        optimizer.zero_grad(set_to_none=True)
                    if (step+1) % 100 == 0:
                        row = {'mode': mode, 'epoch': epoch+1, 'batch': step+1,
                               'batches': len(loader), 'seen': seen, 'epoch_seconds': time.perf_counter()-epoch_start}
                        write_json(report / 'progress.json', row)
                        print(json.dumps(row), flush=True)
                assert seen == len(datasets['train'])
                val, prediction, _ = evaluate(model, val_loader, device, amp=True)
                history.append({'mode': mode, 'epoch': epoch+1, 'train_rows': seen,
                    'validation': val, 'seconds': time.perf_counter()-epoch_start,
                    'class_weights': weights.tolist() if weights is not None else None})
                write_json(report / 'history.json', history)
                print(json.dumps({'mode': mode, 'epoch': epoch+1, 'validation_macro_f1': val['macro_f1']}), flush=True)
                if val['macro_f1'] > best:
                    best, stale = val['macro_f1'], 0
                    save_checkpoint(model, out / mode, root / semantic['transformer']['tokenizer'],
                        {'mode': mode, 'epoch': epoch+1, 'max_length': 512,
                         'canonical_text': semantic['canonical_text'], 'label_to_id': LABEL_TO_ID})
                    np.save(report / f'{mode}_validation.npy', prediction)
                else:
                    stale += 1
                if stale >= cfg['early_stopping_patience']:
                    break
            candidates.append({'spec': {'mode': mode}, 'validation_macro_f1': best})
            del model, optimizer, scheduler, scaler
            gc.collect()
            torch.cuda.empty_cache()
        selected = max(candidates, key=lambda c: c['validation_macro_f1'])
        mode = selected['spec']['mode']
        chosen = out / mode
        lock = {'selected': selected, 'candidates': candidates, 'selection_complete_before_test': True,
                'cache_identity': metadata['identity'], 'checkpoint_sha256': sha256_file(chosen / 'model.safetensors')}
        write_json(report / 'selection_lock.json', lock)
        lock_hash = sha256_file(report / 'selection_lock.json')
        model = BertForSequenceClassification.from_pretrained(chosen, local_files_only=True).to(device)
        _, reloaded, _ = evaluate(model, val_loader, device, amp=True)
        np.testing.assert_array_equal(reloaded, np.load(report / f'{mode}_validation.npy'))
        for split in ('validation', 'test'):
            tick = time.perf_counter()
            if split == 'test':
                loader = DataLoader(datasets[split], batch_size=cfg['eval_batch_size'], collate_fn=collate_tokens)
                _, prediction, _ = evaluate(model, loader, device, amp=True)
                test_seconds = time.perf_counter() - tick
            else:
                prediction = reloaded
            frame = data[split]['frame'][['review_id', 'label_id']].assign(prediction_id=prediction)
            frame.to_parquet(report / f'{split}_predictions.parquet', index=False)
            np.save(report / f'{split}_predictions.npy', prediction)
            write_json(report / f'{split}_metrics.json', metrics(frame.label_id, prediction))
        assert sha256_file(report / 'selection_lock.json') == lock_hash
    result = {'status': 'PASS', 'experiment': 'E05_transformer', 'train_rows': len(datasets['train']),
        'data_regime': 'FULL', 'selected_spec': selected['spec'], 'validation_macro_f1': selected['validation_macro_f1'],
        'test_metrics': json.loads((report / 'test_metrics.json').read_text(encoding='utf-8')),
        'runtime_seconds': monitor.seconds, 'peak_process_rss_bytes': monitor.peak_rss_bytes,
        'peak_gpu_allocated_bytes': torch.cuda.max_memory_allocated(), 'test_prediction_seconds': test_seconds,
        'inference_ms_per_review': test_seconds / len(datasets['test']) * 1000,
        'artifact_bytes': sum(p.stat().st_size for p in chosen.iterdir() if p.is_file()),
        'artifact_directory': chosen.relative_to(root).as_posix(), 'test_prediction_passes': 1}
    write_json(report / 'result.json', result)
    return result


if __name__ == '__main__':
    try:
        print(json.dumps(run()))
    except Exception as exc:
        print(json.dumps({'status': 'FAILED', 'error_type': type(exc).__name__, 'error': str(exc)}))
        raise SystemExit(1) from None
