"""Bộ điều hợp PyTorch đã cố định-P4, trình trợ giúp tinh chỉnh rõ ràng và văn bản suy luận."""

import json
import math
import random
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from torch.utils.data import Dataset, Sampler
from transformers import BertForSequenceClassification

from src.evaluation.classification import LABELS, classification_metrics
from src.preprocessing.bert import BertPreprocessor

FEATURES = ('input_ids', 'attention_mask', 'token_type_ids')
LABEL_TO_ID = dict(zip(LABELS, range(3)))


def seed_everything(seed: int) -> None:
    """hạt giống ngẫu nhiên Python/NumPy/Torch; suy luận xác định, phát lại huấn luyện nỗ lực tốt nhất."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.use_deterministic_algorithms(True, warn_only=True)


def resolve_device(requested: str = 'auto') -> torch.device:
    """Lựa chọn CUDA tự động với dự phòng CPU; CUDA rõ ràng không thành công khi vắng mặt."""
    if requested not in ('auto', 'cpu', 'cuda'):
        raise ValueError('device must be auto/cpu/cuda')
    if requested == 'cuda' and not torch.cuda.is_available():
        raise ValueError('CUDA requested but unavailable')
    return torch.device('cuda' if requested != 'cpu' and torch.cuda.is_available() else 'cpu')


class P4BertDataset(Dataset):
    """Giữ riêng ID review; chỉ hiển thị cố định token và nhãn tới mô hình."""

    def __init__(self, records: list[dict], *, split: str, max_length: int, vocab_size: int) -> None:
        if split not in ('train', 'validation', 'test') or not records:
            raise ValueError('Nonempty named split required')
        self.split, self.records = split, []
        self.review_ids, self.labels, self.lengths = [], [], []
        for row in records:
            ids = list(row['input_ids'])
            label = row['label_id']
            if row['split'] != split or not isinstance(label, (int, np.integer)) or label not in (0, 1, 2):
                raise ValueError('Split or label ID mismatch')
            if not 2 <= len(ids) <= max_length or ids[0] != 101 or ids[-1] != 102:
                raise ValueError('P4 CLS/SEP/length policy violated')
            if any(not isinstance(i, (int, np.integer)) or not 0 <= i < vocab_size for i in ids):
                raise ValueError('Token ID outside pretrained vocabulary')
            if list(row['attention_mask']) != [1] * len(ids) or list(row['token_type_ids']) != [0] * len(ids):
                raise ValueError('P4 requires unpadded single-context arrays')
            self.review_ids.append(row['review_id'])
            self.labels.append(int(label))
            self.lengths.append(len(ids))
            self.records.append({**{key: list(row[key]) for key in FEATURES}, 'labels': int(label)})
        if len(set(self.review_ids)) != len(self.review_ids):
            raise ValueError('Duplicate review IDs')

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, index: int) -> dict:
        return {k: list(v) if isinstance(v, list) else v for k, v in self.records[index].items()}


def collate_tokens(records: list[dict]) -> dict[str, torch.Tensor]:
    """Phần đệm bên phải động, phần đệm ID 0; lĩnh vực kế toán không bao giờ đạt được về phía trước."""
    if not records:
        raise ValueError('Empty batch')
    width = max(len(row['input_ids']) for row in records)
    result = {}
    for key in FEATURES:
        result[key] = torch.tensor([list(row[key]) + [0] * (width - len(row[key])) for row in records], dtype=torch.long)
    has_labels = ['labels' in row for row in records]
    if any(has_labels) and not all(has_labels):
        raise ValueError('Mixed labeled/unlabeled batch')
    if all(has_labels):
        result['labels'] = torch.tensor([row['labels'] for row in records], dtype=torch.long)
    return result


class LengthBatchSampler(Sampler):
    """Xô có chiều dài chỉ trên tập huấn luyện được gieo hạt; mọi mẫu đều xuất hiện chính xác once/epoch."""

    def __init__(self, dataset: P4BertDataset, batch_size: int, seed: int, multiplier: int = 32):
        if dataset.split != 'train' or batch_size < 1 or multiplier < 1:
            raise ValueError('Train-only sampler and positive batch settings required')
        self.dataset, self.batch_size, self.seed, self.multiplier = dataset, batch_size, seed, multiplier
        self.epoch = 0

    def __len__(self) -> int:
        return math.ceil(len(self.dataset) / self.batch_size)

    def __iter__(self):
        rng = random.Random(self.seed + self.epoch)
        indices = list(range(len(self.dataset)))
        rng.shuffle(indices)
        bucket_size = self.batch_size * self.multiplier
        batches = []
        for start in range(0, len(indices), bucket_size):
            bucket = sorted(indices[start:start + bucket_size], key=lambda i: self.dataset.lengths[i])
            batches.extend(bucket[i:i + self.batch_size] for i in range(0, len(bucket), self.batch_size))
        rng.shuffle(batches)
        yield from batches


def class_weights(dataset: P4BertDataset, mode: str) -> torch.Tensor | None:
    """Tần số nghịch đảo cân bằng chỉ từ tập huấn luyện; trọng lượng dự kiến ​​bằng một."""
    if dataset.split != 'train':
        raise ValueError('Weights require train-only labels')
    if mode == 'unweighted':
        return None
    if mode != 'balanced':
        raise ValueError('Unsupported weighting mode')
    counts = np.bincount(dataset.labels, minlength=3)
    if not counts.all():
        raise ValueError('All training classes required')
    return torch.tensor(len(dataset) / (3 * counts), dtype=torch.float32)


def training_loss(logits: torch.Tensor, labels: torch.Tensor, weights=None) -> torch.Tensor:
    """Trọng số trung bình trên mỗi ví dụ CE; đồng phục tập xác thực hàm mất mát vẫn có thể so sánh được."""
    losses = F.cross_entropy(logits.float(), labels, reduction='none')
    return (losses if weights is None else losses * weights[labels]).mean()


def improved(candidate: dict, incumbent: dict | None) -> bool:
    """Chỉ macro F1 tập xác thực; bảo quản điểm lưu mô hình trước đó trên các mối nối chính xác."""
    return incumbent is None or candidate['macro_f1'] > incumbent['macro_f1']


@torch.inference_mode()
def evaluate(model, loader, device: torch.device, *, amp: bool = False) -> tuple[dict, np.ndarray, np.ndarray]:
    """Đánh giá theo thứ tự bộ tải với CE thống nhất, không phân biệt chế độ tập huấn luyện hàm mất mát."""
    model.eval()
    truth, predictions, loss_sum = [], [], 0.0
    for batch in loader:
        batch = {key: value.to(device) for key, value in batch.items()}
        labels = batch.pop('labels')
        with torch.autocast(device_type=device.type, dtype=torch.float16, enabled=amp and device.type == 'cuda'):
            logits = model(**batch).logits
        loss_sum += F.cross_entropy(logits.float(), labels, reduction='sum').item()
        predictions.extend(logits.argmax(-1).cpu().tolist())
        truth.extend(labels.cpu().tolist())
    result = classification_metrics(truth, predictions)
    result['macro_precision'] = float(np.mean([v['precision'] for v in result['per_class'].values()]))
    result['macro_recall'] = float(np.mean([v['recall'] for v in result['per_class'].values()]))
    result['loss'] = loss_sum / len(truth)
    return result, np.asarray(predictions), np.asarray(truth)


class BertArtifact:
    """Đã lưu văn bản BERT suy luận với chính sách P4 bộ tách token ban đầu."""

    def __init__(self, directory: Path, device: str = 'auto') -> None:
        from src.data.acquisition import sha256_file
        self.directory = Path(directory)
        metadata = json.loads((self.directory / 'metadata.json').read_text(encoding='utf-8'))
        if metadata['label_to_id'] != LABEL_TO_ID:
            raise ValueError('Invalid saved label map')
        for relative, digest in metadata['files_sha256'].items():
            if sha256_file(self.directory / relative) != digest:
                raise ValueError(f'Changed BERT artifact: {relative}')
        self.device = resolve_device(device)
        self.model = BertForSequenceClassification.from_pretrained(self.directory, local_files_only=True).to(self.device).eval()
        if self.model.config.label2id != LABEL_TO_ID or self.model.config.num_labels != 3:
            raise ValueError('Model label map differs')
        self.preprocessor = BertPreprocessor(self.directory / 'tokenizer.json', metadata['max_length'])

    @torch.inference_mode()
    def predict_ids(self, frame: pd.DataFrame, batch_size: int = 16) -> np.ndarray:
        if frame.empty or batch_size < 1:
            raise ValueError('Nonempty reviews and positive batch size required')
        output = []
        for start in range(0, len(frame), batch_size):
            rows = self.preprocessor.encode(frame.iloc[start:start + batch_size])
            batch = {key: value.to(self.device) for key, value in collate_tokens(rows).items()}
            output.extend(self.model(**batch).logits.argmax(-1).cpu().tolist())
        return np.asarray(output, dtype=int)

    def predict(self, frame: pd.DataFrame, batch_size: int = 16) -> list[dict]:
        return [{'domain': 'laptop', 'language': 'en', 'sentiment': LABELS[i],
                 'confidence': None, 'aspects': []} for i in self.predict_ids(frame, batch_size)]
