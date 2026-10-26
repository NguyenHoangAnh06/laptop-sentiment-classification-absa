"""Huấn luyện TabM trên dense embedding; selection chỉ dùng validation."""

import time

import numpy as np
import torch
import torch.nn.functional as F

from src.evaluation.classification import classification_metrics


def balanced_weights(labels: np.ndarray) -> np.ndarray:
    counts = np.bincount(labels, minlength=3)
    if (counts == 0).any():
        raise ValueError('Train phải có đủ ba lớp')
    return (len(labels) / (3 * counts)).astype(np.float32)


def make_tabm(dimension: int, config: dict, device: str):
    from tabm import TabM
    return TabM.make(n_num_features=dimension, d_out=3, n_blocks=config['n_blocks'],
                     d_block=config['d_block'], k=config['k'], dropout=config['dropout']).to(device)


def tabm_predict(model, matrix: np.ndarray, *, device: str, batch_size: int = 256) -> np.ndarray:
    model.eval()
    predictions = []
    with torch.inference_mode():
        for start in range(0, len(matrix), batch_size):
            values = torch.tensor(np.array(matrix[start:start+batch_size]), device=device)
            probabilities = model(values).softmax(-1).mean(1)
            predictions.extend(probabilities.argmax(-1).cpu().tolist())
    return np.array(predictions, dtype='int64')


def train_tabm(train_x, train_y, validation_x, validation_y, *, config: dict,
               device: str, weighted: bool, max_seconds: float, memory_limit: int):
    """Mỗi ensemble member học CE riêng; suy luận trung bình xác suất theo tài liệu TabM."""
    import psutil
    model = make_tabm(train_x.shape[1], config, device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=config['learning_rate'],
                                 weight_decay=config['weight_decay'])
    weights = torch.tensor(balanced_weights(train_y), device=device) if weighted else None
    train_tensor = torch.tensor(np.array(train_x), device=device)
    labels_tensor = torch.tensor(train_y, device=device)
    # Smoke không optimizer.step; xóa gradient trước full, không học từ validation/test.
    logits = model(train_tensor[:3])
    F.cross_entropy(logits.flatten(0, 1), labels_tensor[:3].repeat_interleave(logits.shape[1]), weight=weights).backward()
    optimizer.zero_grad(set_to_none=True)
    if device == 'cuda':
        torch.cuda.synchronize()
        print(f'TabM smoke PASS peak_gpu_allocated_bytes={torch.cuda.max_memory_allocated()}', flush=True)
    best, best_state, history, stale = -1., None, [], 0
    started = time.perf_counter()
    for epoch in range(config['epochs']):
        model.train()
        order = torch.randperm(len(train_y), device=device)
        loss_sum = 0.
        for indices in order.split(config['batch_size']):
            if time.perf_counter() - started > max_seconds or psutil.Process().memory_info().rss > memory_limit:
                raise RuntimeError('Vượt trần runtime/RSS TabM; không dùng kết quả chưa hoàn chỉnh')
            optimizer.zero_grad(set_to_none=True)
            logits = model(train_tensor[indices])
            targets = labels_tensor[indices].repeat_interleave(logits.shape[1])
            loss = F.cross_entropy(logits.flatten(0, 1), targets, weight=weights)
            loss.backward()
            optimizer.step()
            loss_sum += float(loss.detach()) * len(indices)
        prediction = tabm_predict(model, validation_x, device=device, batch_size=config['batch_size'])
        metrics = classification_metrics(validation_y, prediction)
        history.append({'epoch': epoch+1, 'loss': loss_sum/len(train_y), 'macro_f1': metrics['macro_f1'],
                        'per_class_f1': {k: v['f1'] for k, v in metrics['per_class'].items()},
                        'seconds': time.perf_counter()-started,
                        'gpu_allocated_bytes': torch.cuda.max_memory_allocated() if device == 'cuda' else None})
        print(f'TabM weighted={weighted} epoch={epoch+1} macro_f1={metrics["macro_f1"]:.6f}', flush=True)
        if metrics['macro_f1'] > best + 1e-12:
            best = metrics['macro_f1']
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            stale = 0
        else:
            stale += 1
        if stale >= config['patience']:
            break
    model.load_state_dict(best_state)
    return model, history
