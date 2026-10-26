"""Số liệu ba lớp cố định và phép đo bộ nhớ quy trình rõ ràng."""

import threading
import time

import numpy as np
import psutil
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support

LABELS = ('negative', 'neutral', 'positive')


def classification_metrics(y_true, y_pred) -> dict:
    """Báo cáo tất cả các lớp, bao gồm cả dự đoán vắng mặt, có số chia bằng 0 = 0."""
    truth, predicted = np.asarray(y_true), np.asarray(y_pred)
    if truth.ndim != 1 or truth.shape != predicted.shape or not len(truth):
        raise ValueError('Nonempty aligned one-dimensional labels required')
    if not np.isin(truth, [0, 1, 2]).all() or not np.isin(predicted, [0, 1, 2]).all():
        raise ValueError('Only label IDs 0/1/2 supported')
    precision, recall, f1, support = precision_recall_fscore_support(
        truth, predicted, labels=[0, 1, 2], zero_division=0)
    return {
        'accuracy': float(accuracy_score(truth, predicted)),
        'macro_f1': float(f1.mean()),
        'weighted_f1': float(np.average(f1, weights=support)),
        'per_class': {label: {'precision': float(precision[i]), 'recall': float(recall[i]),
                             'f1': float(f1[i]), 'support': int(support[i])}
                      for i, label in enumerate(LABELS)},
        'confusion_matrix': confusion_matrix(truth, predicted, labels=[0, 1, 2]).tolist(),
        'confusion_matrix_order': list(LABELS),
    }


class ResourceMonitor:
    """Mẫu RSS toàn bộ quá trình; giới hạn được kiểm tra giữa các hoạt động giới hạn.

    Đây không phải là phân bổ dành riêng cho công cụ ước tính hoặc giới hạn memory/time của hệ điều hành cứng.
    """

    def __enter__(self):
        self.process = psutil.Process()
        self.start = time.perf_counter()
        self.peak_rss_bytes = self.process.memory_info().rss
        self.stopped = threading.Event()
        self.thread = threading.Thread(target=self._sample, daemon=True)
        self.thread.start()
        return self

    def _sample(self):
        while not self.stopped.wait(.02):
            self.peak_rss_bytes = max(self.peak_rss_bytes, self.process.memory_info().rss)

    def __exit__(self, *exc):
        self.peak_rss_bytes = max(self.peak_rss_bytes, self.process.memory_info().rss)
        self.stopped.set()
        self.thread.join()
        self.seconds = time.perf_counter() - self.start


def flat_metrics(metrics: dict) -> dict:
    """Làm phẳng các số liệu vô hướng và mỗi lớp cho các bảng CSV có thể so sánh được."""
    row = {key: metrics[key] for key in ('accuracy', 'macro_f1', 'weighted_f1')}
    for label, values in metrics['per_class'].items():
        row.update({f'{label}_{key}': value for key, value in values.items()})
    return row
