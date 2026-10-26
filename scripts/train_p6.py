"""BERT tinh chỉnh đầy đủ trên P4 các tập đã chia với lựa chọn điểm lưu mô hình chỉ tập xác thực."""

import argparse
import gc
import importlib.metadata
import json
import math
import os
import platform
import shutil
import sys
import time
from pathlib import Path

os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')
os.environ.setdefault('CUBLAS_WORKSPACE_CONFIG', ':4096:8')

import numpy as np
import pandas as pd
import psutil
import torch
import torch.nn.functional as F
import yaml
from huggingface_hub import hf_hub_download
from torch.utils.data import DataLoader
from transformers import BertConfig, BertForSequenceClassification, get_linear_schedule_with_warmup
from transformers.utils import logging as hf_logging

hf_logging.disable_progress_bar()

from scripts.train_p5 import error_diagnostics, protected_inputs, validate_isolation, write_json
from src.config import PROJECT_ROOT
from src.data.acquisition import sha256_file
from src.evaluation.classification import LABELS, ResourceMonitor, flat_metrics
from src.preprocessing.bert import BertPreprocessor
from src.sentiment.bert import (FEATURES, LABEL_TO_ID, BertArtifact, LengthBatchSampler,
    P4BertDataset, class_weights, collate_tokens, evaluate, improved, resolve_device,
    seed_everything, training_loss)


def validate_inputs(root: Path, cfg: dict, p4: dict) -> tuple[dict, dict, dict]:
    """Xác minh mọi hàng BERT token với P4 và bộ tiền xử lý tối thiểu đã cố định của nó."""
    pre_dir = root / p4['paths']['preprocessing']
    prep = json.loads((pre_dir / 'preprocessing.json').read_text(encoding='utf-8'))
    if cfg['max_length'] != prep['bert']['max_length_policy']['max_length']:
        raise ValueError('P4 train-derived max length must remain unchanged')
    if cfg['checkpoint'] != prep['bert']['repo'] or cfg['revision'] != prep['bert']['revision']:
        raise ValueError('Pretrained source must match P4 tokenizer')
    model_config = BertConfig.from_json_file(pre_dir / 'bert/config.json')
    tokenizer = BertPreprocessor(pre_dir / 'bert/tokenizer.json', cfg['max_length'])
    if tokenizer.tokenizer.get_vocab_size() != model_config.vocab_size or model_config.pad_token_id != 0:
        raise ValueError('Tokenizer/model vocabulary incompatibility')
    datasets, frames = {}, {}
    columns = ['review_id', 'label_id', 'split', 'parent_asin', 'asin', 'split_group_id',
               'text', 'language', 'sentiment', 'label_provenance', 'clean_text_sha256', 'rating']
    for split in ('train', 'validation', 'test'):
        frame = pd.read_parquet(root / p4['paths']['splits'] / f'{split}.parquet', columns=columns)
        records = pd.read_parquet(root / p4['paths']['features'] / f'{split}_bert.parquet').to_dict('records')
        dataset = P4BertDataset(records, split=split, max_length=cfg['max_length'], vocab_size=model_config.vocab_size)
        if dataset.review_ids != frame.review_id.tolist() or dataset.labels != frame.label_id.tolist():
            raise ValueError('P4 token row ID/label order mismatch')
        if frame.sentiment.tolist() != [LABELS[i] for i in dataset.labels] or not frame.label_provenance.eq('rating-derived proxy').all():
            raise ValueError('Target map/provenance mismatch')
        for start in range(0, len(frame), 128):
            encoded = tokenizer.encode(frame.iloc[start:start + 128])
            for actual, expected in zip(dataset.records[start:start + 128], encoded):
                if any(actual[key] != expected[key] for key in FEATURES):
                    raise ValueError('Frozen tokenizer differs from P4 arrays')
        datasets[split], frames[split] = dataset, frame
    isolation = validate_isolation(frames)
    return datasets, frames, {'status': 'PASS', 'full_token_reencode': 'PASS', 'isolation': isolation,
        'max_length': cfg['max_length'], 'vocab_size': model_config.vocab_size,
        'counts': {s: {'rows': len(d), 'classes': np.bincount(d.labels, minlength=3).tolist()} for s, d in datasets.items()}}


def save_checkpoint(model, directory: Path, tokenizer_path: Path, metadata: dict) -> None:
    """Giữ một điểm lưu mô hình tốt nhất cho mỗi ứng viên, thay thế các tệp riêng lẻ của nó một cách nguyên tử."""
    directory.mkdir(parents=True, exist_ok=True)
    temporary = directory / '_saving'
    temporary.mkdir(exist_ok=False)
    model.save_pretrained(temporary, safe_serialization=True)
    shutil.copyfile(tokenizer_path, temporary / 'tokenizer.json')
    metadata = {**metadata, 'label_to_id': LABEL_TO_ID,
                'files_sha256': {p.name: sha256_file(p) for p in temporary.iterdir() if p.is_file()}}
    write_json(temporary / 'metadata.json', metadata)
    for item in temporary.iterdir():
        item.replace(directory / item.name)
    temporary.rmdir()


def smoke_test(model, dataset, device, amp: bool) -> dict:
    """đã huấn luyện trước forward/backward thực chỉ trên tập huấn luyện; người gọi tải lại trước khi khớp mô hình đầy."""
    indices = [dataset.labels.index(i) for i in range(3)]
    batch = {k: v.to(device) for k, v in collate_tokens([dataset[i] for i in indices]).items()}
    labels = batch.pop('labels')
    model.train()
    with torch.autocast(device_type=device.type, dtype=torch.float16, enabled=amp):
        logits = model(**batch).logits
        loss = training_loss(logits, labels)
    loss.backward()
    if not torch.isfinite(loss) or not all(torch.isfinite(p.grad).all() for p in model.parameters() if p.grad is not None):
        raise ValueError('Nonfinite smoke loss/gradient')
    if logits.shape != (3, 3) or not any(p.grad is not None for p in model.bert.parameters()):
        raise ValueError('Full BERT backward path missing')
    model.zero_grad(set_to_none=True)
    return {'status': 'PASS', 'loss': loss.item(), 'logits_shape': list(logits.shape),
            'backbone_gradient': True, 'data': '3 real train samples; no optimizer update'}


def run(config_path: Path, root: Path = PROJECT_ROOT) -> dict:
    cfg = yaml.safe_load(config_path.read_text(encoding='utf-8'))
    suffix = cfg['output_suffix']
    if not suffix or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in suffix):
        raise ValueError('Invalid output suffix')
    out, report = root / 'artifacts/models' / suffix, root / 'reports/p6' / suffix
    if out.exists() or report.exists():
        raise FileExistsError('Fresh suffix required; never overwrite a completed/partial run')
    if cfg['loss_candidates'] != ['unweighted', 'balanced']:
        raise ValueError('Declared unweighted/balanced comparison required')
    p4 = json.loads((root / cfg['p4_manifest']).read_text(encoding='utf-8'))
    p5 = json.loads((root / cfg['p5_manifest']).read_text(encoding='utf-8'))
    if p5['status'] != 'DONE':
        raise ValueError('P5 dependency not complete')
    out.mkdir(parents=True)
    report.mkdir(parents=True)
    started = time.perf_counter()
    device = resolve_device(cfg['device'])
    amp = device.type == 'cuda' and cfg['mixed_precision'] == 'fp16'
    torch.set_num_threads(cfg['threads'])

    def guard():
        if time.perf_counter() - started > cfg['max_seconds']:
            raise RuntimeError('P6 runtime budget exceeded')
        if psutil.Process().memory_info().rss > cfg['max_process_rss_bytes']:
            raise RuntimeError('P6 process RAM budget exceeded')

    try:
        with ResourceMonitor() as total:
            inputs = protected_inputs(root, p4)
            inputs.update(p5['input_sha256'])
            inputs.update(p5['output_sha256'])
            inputs.update(p5['implementation_sha256'])
            for rel in (cfg['p4_manifest'], cfg['p5_manifest']):
                inputs[rel] = sha256_file(root / rel)
            for rel, digest in inputs.items():
                if sha256_file(root / rel) != digest:
                    raise ValueError(f'Changed P4/P5 input: {rel}')
            datasets, frames, input_checks = validate_inputs(root, cfg, p4)
            write_json(report / 'input_validation.json', input_checks)
            write_json(report / 'config.json', cfg)
            environment = {'python': sys.version, 'platform': platform.platform(), 'device': str(device),
                'cuda_runtime': torch.version.cuda, 'amp': amp, 'available_ram_bytes': psutil.virtual_memory().available,
                'disk_free_bytes': shutil.disk_usage(root).free, 'threads': cfg['threads'],
                'packages': {p: importlib.metadata.version(p) for p in
                             ('torch', 'transformers', 'tokenizers', 'safetensors', 'huggingface-hub', 'scikit-learn')},
                'cuda_device': torch.cuda.get_device_name() if device.type == 'cuda' else None,
                'vram_total_bytes': torch.cuda.get_device_properties(device).total_memory if device.type == 'cuda' else None}
            write_json(report / 'environment.json', environment)
            print(json.dumps(environment), flush=True)
            pre_dir = root / p4['paths']['preprocessing']
            source = Path(hf_hub_download(cfg['checkpoint'], 'model.safetensors', revision=cfg['revision']))
            write_json(report / 'pretrained_source.json', {'checkpoint': cfg['checkpoint'], 'revision': cfg['revision'],
                'filename': 'model.safetensors', 'sha256': sha256_file(source), 'bytes': source.stat().st_size,
                'declared_license': 'apache-2.0', 'source': 'https://huggingface.co/' + cfg['checkpoint'],
                'model_card': 'https://huggingface.co/' + cfg['checkpoint'] + '/blob/' + cfg['revision'] + '/README.md'})
            model_cfg = BertConfig.from_json_file(pre_dir / 'bert/config.json')
            model_cfg.num_labels = 3
            model_cfg.label2id = LABEL_TO_ID
            model_cfg.id2label = dict(enumerate(LABELS))
            model_cfg.problem_type = 'single_label_classification'
            def fresh_model():
                seed_everything(cfg['seed'])
                model, info = BertForSequenceClassification.from_pretrained(
                    source.parent, config=model_cfg, local_files_only=True, output_loading_info=True,
                    attn_implementation='sdpa')
                missing = set(info.get('missing_keys', []))
                if missing - {'classifier.weight', 'classifier.bias'}:
                    raise ValueError(f'Unexpected missing pretrained parameters: {missing}')
                write_json(report / 'pretrained_loading.json', {
                    key: sorted(value) if isinstance(value, set) else value for key, value in info.items()})
                model.to(device)
                if cfg['gradient_checkpointing']:
                    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant': False})
                return model
            model = fresh_model()
            write_json(report / 'smoke.json', smoke_test(model, datasets['train'], device, amp))
            del model
            gc.collect()
            if device.type == 'cuda':
                torch.cuda.empty_cache()
                torch.cuda.reset_peak_memory_stats()
            guard()
            val_loader = DataLoader(datasets['validation'], batch_size=cfg['eval_batch_size'], shuffle=False,
                                    collate_fn=collate_tokens, num_workers=0)
            history, choices = [], []
            all_training_started = time.perf_counter()
            for mode in cfg['loss_candidates']:
                guard()
                model = fresh_model()
                weights = class_weights(datasets['train'], mode)
                weights = weights.to(device) if weights is not None else None
                sampler = LengthBatchSampler(datasets['train'], cfg['batch_size'], cfg['seed'], cfg['bucket_multiplier'])
                loader = DataLoader(datasets['train'], batch_sampler=sampler, collate_fn=collate_tokens, num_workers=0)
                optimizer = torch.optim.AdamW(model.parameters(), lr=cfg['learning_rate'], weight_decay=cfg['weight_decay'])
                steps = math.ceil(len(loader) / cfg['gradient_accumulation']) * cfg['epochs']
                scheduler = get_linear_schedule_with_warmup(optimizer, math.ceil(steps * cfg['warmup_ratio']), steps)
                scaler = torch.amp.GradScaler('cuda', enabled=amp)
                best, best_epoch, stale, candidate_start = None, None, 0, time.perf_counter()
                candidate_dir = out / mode
                for epoch in range(1, cfg['epochs'] + 1):
                    guard()
                    sampler.epoch = epoch - 1
                    model.train()
                    optimizer.zero_grad(set_to_none=True)
                    loss_total, seen, updates, skipped = 0.0, 0, 0, 0
                    epoch_started = time.perf_counter()
                    for step, batch in enumerate(loader):
                        guard()
                        batch = {k: v.to(device) for k, v in batch.items()}
                        labels = batch.pop('labels')
                        # Nhóm tích lũy cuối cùng có thể chứa ít hơn vi lô đã định cấu hình.
                        group_start = (step // cfg['gradient_accumulation']) * cfg['gradient_accumulation']
                        group_size = min(cfg['gradient_accumulation'], len(loader) - group_start)
                        with torch.autocast(device_type=device.type, dtype=torch.float16, enabled=amp):
                            logits = model(**batch).logits
                            loss = training_loss(logits, labels, weights)
                        if not torch.isfinite(loss):
                            raise ValueError('Nonfinite train loss')
                        scaler.scale(loss / group_size).backward()
                        loss_total += loss.detach().item() * len(labels)
                        seen += len(labels)
                        if (step + 1) % cfg['gradient_accumulation'] == 0 or step + 1 == len(loader):
                            scaler.unscale_(optimizer)
                            torch.nn.utils.clip_grad_norm_(model.parameters(), cfg['max_grad_norm'])
                            old_scale = scaler.get_scale()
                            scaler.step(optimizer)
                            scaler.update()
                            if scaler.get_scale() >= old_scale:
                                scheduler.step()
                                updates += 1
                            else:
                                skipped += 1
                            optimizer.zero_grad(set_to_none=True)
                        if (step + 1) % cfg['log_steps'] == 0:
                            message = {'mode': mode, 'epoch': epoch, 'microbatch': step + 1, 'batches': len(loader),
                                'seen': seen, 'loss': loss_total / seen, 'epoch_seconds': time.perf_counter() - epoch_started}
                            write_json(report / 'progress.json', message)
                            print(json.dumps(message), flush=True)
                    if seen != len(datasets['train']):
                        raise ValueError('Full train epoch did not conserve sample count')
                    train_seconds = time.perf_counter() - epoch_started
                    validation, _, _ = evaluate(model, val_loader, device)
                    row = {'mode': mode, 'epoch': epoch, 'train_rows': seen, 'train_loss': loss_total / seen,
                        'validation': validation, 'training_seconds': train_seconds,
                        'epoch_total_seconds': time.perf_counter() - epoch_started,
                        'optimizer_updates': updates, 'amp_skipped_updates': skipped,
                        'class_weights': weights.cpu().tolist() if weights is not None else None}
                    history.append(row)
                    write_json(report / 'training_history.json', history)
                    print(json.dumps({'mode': mode, 'epoch': epoch, 'validation': validation}), flush=True)
                    if improved(validation, best):
                        best, best_epoch, stale = validation, epoch, 0
                        save_checkpoint(model, candidate_dir, pre_dir / 'bert/tokenizer.json', {
                            'checkpoint': cfg['checkpoint'], 'revision': cfg['revision'], 'seed': cfg['seed'],
                            'mode': mode, 'best_epoch': epoch, 'max_length': cfg['max_length'],
                            'fit_split': 'train', 'fit_rows': seen, 'selection_split': 'validation',
                            'validation': best, 'class_weights': row['class_weights'], 'confidence': None})
                    else:
                        stale += 1
                    if stale >= cfg['early_stopping_patience']:
                        break
                choices.append({'mode': mode, 'validation': best, 'best_epoch': best_epoch,
                                'candidate_total_seconds': time.perf_counter() - candidate_start,
                                'training_seconds': sum(r['training_seconds'] for r in history if r['mode'] == mode)})
                del model, optimizer, scheduler, scaler
                gc.collect()
                if device.type == 'cuda':
                    torch.cuda.empty_cache()
            search_seconds = time.perf_counter() - all_training_started
            selected = max(choices, key=lambda c: c['validation']['macro_f1'])
            selected_dir = out / selected['mode']
            lock = {'selection_metric': 'validation macro_f1', 'candidate_choices': choices,
                'selected': selected, 'test_prediction_passes_planned': 1,
                'config_sha256': sha256_file(config_path), 'checkpoint_sha256': sha256_file(selected_dir / 'model.safetensors')}
            write_json(report / 'selection_lock.json', lock)
            lock_digest = sha256_file(report / 'selection_lock.json')
            artifact = BertArtifact(selected_dir, str(device))
            reloaded_val, val_predictions, _ = evaluate(artifact.model, val_loader, device)
            if not np.isclose(reloaded_val['macro_f1'], selected['validation']['macro_f1'], atol=1e-12):
                raise ValueError('Reloaded best checkpoint validation differs')
            test_loader = DataLoader(datasets['test'], batch_size=cfg['eval_batch_size'], shuffle=False,
                                     collate_fn=collate_tokens, num_workers=0)
            evaluation_start = time.perf_counter()
            test_metrics, predicted, truth = evaluate(artifact.model, test_loader, device)
            test_seconds = time.perf_counter() - evaluation_start
            write_json(report / 'metrics.json', {'validation': reloaded_val, 'test': test_metrics})
            for name, values in (('validation', reloaded_val), ('test', test_metrics)):
                pd.DataFrame(values['confusion_matrix'], index=LABELS, columns=LABELS).rename_axis('true_label').to_csv(
                    report / f'{name}_confusion_matrix.csv')
            pd.DataFrame({'review_id': datasets['test'].review_ids, 'label_id': truth, 'prediction_id': predicted}).to_parquet(
                out / 'test_predictions.parquet', index=False)
            pd.DataFrame({'review_id': datasets['validation'].review_ids, 'label_id': datasets['validation'].labels,
                          'prediction_id': val_predictions}).to_parquet(out / 'validation_predictions.parquet', index=False)
            batch = frames['validation'].iloc[:cfg['latency_batch_size']]
            # Tính chẵn lẻ tải lại sử dụng FP32 suy luận vì tệp kết quả đã xuất hứa hẹn FP32 xác định.
            expected = artifact.predict_ids(batch, cfg['eval_batch_size'])
            np.testing.assert_array_equal(expected, artifact.predict_ids(batch, cfg['eval_batch_size']))
            latency = []
            for _ in range(cfg['latency_repeats']):
                if device.type == 'cuda': torch.cuda.synchronize()
                tick = time.perf_counter()
                artifact.predict_ids(batch, cfg['eval_batch_size'])
                if device.type == 'cuda': torch.cuda.synchronize()
                latency.append(time.perf_counter() - tick)
            p5_report = root / cfg['p5_manifest']
            benchmark = pd.read_csv(p5_report.parent / 'benchmark.csv')
            artifact_bytes = sum(p.stat().st_size for p in selected_dir.iterdir() if p.is_file())
            bert_row = {'model': 'bert', 'selected_by_validation': False,
                'validation_macro_f1': reloaded_val['macro_f1'], **flat_metrics(test_metrics),
                'training_seconds': selected['training_seconds'], 'search_training_seconds': sum(c['training_seconds'] for c in choices),
                'search_total_seconds': search_seconds, 'test_prediction_seconds': test_seconds,
                'inference_latency_ms_per_review': float(np.median(latency) * 1000 / len(batch)),
                'latency_batch_size': len(batch), 'latency_repeats': len(latency),
                'model_bytes': (selected_dir / 'model.safetensors').stat().st_size,
                'inference_artifact_bytes': artifact_bytes, 'peak_process_rss_bytes': total.peak_rss_bytes,
                'peak_vram_allocated_bytes': torch.cuda.max_memory_allocated() if device.type == 'cuda' else None,
                'peak_vram_reserved_bytes': torch.cuda.max_memory_reserved() if device.type == 'cuda' else None}
            benchmark['selected_by_validation'] = False
            benchmark = pd.concat([benchmark, pd.DataFrame([bert_row])], ignore_index=True)
            benchmark.loc[benchmark.validation_macro_f1.idxmax(), 'selected_by_validation'] = True
            benchmark.to_csv(report / 'benchmark.csv', index=False)
            diag, queue = error_diagnostics(frames['test'], predicted, cfg['seed'])
            queue.to_parquet(out / 'error_review_queue.parquet', index=False)
            lr = pd.read_parquet(
                root / 'artifacts/models' / p5_report.parent.name / 'test_predictions.parquet')
            if lr.review_id.tolist() != datasets['test'].review_ids:
                raise ValueError('LR comparison IDs not aligned')
            lr_errors = lr.logistic_regression.to_numpy() != truth
            bert_errors = predicted != truth
            diag['paired_lr_proxy_errors'] = {'both_wrong': int((lr_errors & bert_errors).sum()),
                'bert_only_wrong': int((~lr_errors & bert_errors).sum()), 'lr_only_wrong': int((lr_errors & ~bert_errors).sum()),
                'both_correct': int((~lr_errors & ~bert_errors).sum())}
            write_json(report / 'error_analysis.json', diag)
            if sha256_file(report / 'selection_lock.json') != lock_digest:
                raise ValueError('Selection changed after test')
            for rel, digest in inputs.items():
                if sha256_file(root / rel) != digest:
                    raise ValueError(f'Protected input changed: {rel}')
            guard()
            if sum(p.stat().st_size for d in (out, report) for p in d.rglob('*') if p.is_file()) > cfg['max_output_bytes']:
                raise RuntimeError('Output budget exceeded')
            write_json(report / 'validation.json', {'status': 'PASS', 'protected_inputs_unchanged': len(inputs),
                'reload_validation_macro_f1': reloaded_val['macro_f1'], 'deterministic_text_inference': 'PASS',
                'test_prediction_passes': 1, 'test_used_for_selection': False})
        result = {'status': 'DONE', 'phase': 'P6', 'selected': selected,
            'runtime_seconds': total.seconds, 'peak_process_rss_bytes': total.peak_rss_bytes,
            'input_sha256': inputs, 'selection_lock_sha256': lock_digest,
            'output_sha256': {p.relative_to(root).as_posix(): sha256_file(p) for d in (out, report) for p in d.rglob('*') if p.is_file()},
            'implementation_sha256': {p: sha256_file(root / p) for p in
                ('scripts/train_p6.py', 'src/sentiment/bert.py', 'configs/p6.yaml', 'src/models/registry.py', 'requirements.txt')},
            'gold_created': False, 'P7_executed': False}
        write_json(report / 'manifest.json', result)
        return result
    except Exception as exc:
        write_json(report / 'status.json', {'status': 'BLOCKED', 'BLOCKED': str(exc),
            'NEXT_ACTION': 'Inspect preserved best checkpoints/history; fix cause and use a new suffix. Never tune from test.'})
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=PROJECT_ROOT / 'configs/p6.yaml')
    args = parser.parse_args()
    result = run(args.config)
    print(json.dumps({k: result[k] for k in ('status', 'selected', 'runtime_seconds', 'peak_process_rss_bytes')}))


if __name__ == '__main__':
    main()
