"""Công cụ ước tính cổ điển và cảm xúc các tệp kết quả chỉ có thể tải lại văn bản."""

from dataclasses import dataclass
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.tree import DecisionTreeClassifier

from src.evaluation.classification import LABELS


def make_estimator(name: str, params: dict, seed: int):
    """Xây dựng một công cụ ước tính hạt giống; TF-IDF thưa thớt không bao giờ được tăng cường."""
    if name == 'majority':
        return DummyClassifier(strategy='most_frequent', random_state=seed, **params)
    if name == 'logistic_regression':
        return LogisticRegression(solver='lbfgs', max_iter=1000, random_state=seed, **params)
    if name == 'linear_svm':
        return LinearSVC(dual='auto', max_iter=10000, random_state=seed, **params)
    if name == 'decision_tree':
        if params.get('max_depth') is None or params.get('min_samples_leaf', 1) < 2:
            raise ValueError('Decision Tree requires bounded depth and min_samples_leaf >= 2')
        return DecisionTreeClassifier(random_state=seed, **params)
    raise ValueError(f'Unsupported classical model: {name}')


def select_candidate(candidates: list[dict]) -> dict:
    """Chỉ chọn theo macro F1 của tập xác thực; quan hệ chính xác sử dụng thứ tự lưới khai báo."""
    eligible = [row for row in candidates if not row['convergence_warning']]
    if not eligible:
        raise ValueError('No converged candidate available')
    return max(eligible, key=lambda row: row['validation']['macro_f1'])


@dataclass
class ClassicalArtifact:
    """Chia sẻ bộ tiền xử lý đã cố định P4 trên các bộ ước tính mà không cần sao chép nó."""

    preprocessor: object
    estimator: object
    metadata: dict

    def predict_ids(self, frame: pd.DataFrame) -> np.ndarray:
        """Dự đoán chỉ sử dụng văn bản review; từ chối đầu vào unsupported/empty trong P4."""
        if frame.empty:
            raise ValueError('At least one review required')
        return self.estimator.predict(self.preprocessor.transform(frame)).astype(int)

    def predict(self, frame: pd.DataFrame) -> list[dict]:
        """Những dự đoán chỉ mang tính tổng thể, không có khía cạnh nào được phát minh hoặc độ tin cậy được hiệu chỉnh."""
        return [{'domain': 'laptop', 'language': 'en', 'sentiment': LABELS[i],
                 'confidence': None, 'aspects': []} for i in self.predict_ids(frame)]


def load_classical(model_dir: Path, root: Path) -> ClassicalArtifact:
    """Tải các tệp kết quả cục bộ đáng tin cậy và xác minh liên kết preprocessing/version được chia sẻ."""
    import json
    import sklearn
    from src.data.acquisition import sha256_file

    model_dir, root = Path(model_dir), Path(root)
    metadata = json.loads((model_dir / 'metadata.json').read_text(encoding='utf-8'))
    if metadata['sklearn_version'] != sklearn.__version__:
        raise ValueError('Use the recorded scikit-learn version to reload artifacts')
    if metadata['label_to_id'] != dict(zip(LABELS, range(3))):
        raise ValueError('Unexpected label mapping')
    pre_path = (root / metadata['preprocessor_path']).resolve()
    if not pre_path.is_relative_to(root.resolve()):
        raise ValueError('Preprocessor must be inside project root')
    if sha256_file(pre_path) != metadata['preprocessor_sha256']:
        raise ValueError('Shared preprocessing artifact changed')
    estimator_path = model_dir / 'model.joblib'
    if sha256_file(estimator_path) != metadata['model_sha256']:
        raise ValueError('Model artifact changed')
    return ClassicalArtifact(joblib.load(pre_path), joblib.load(estimator_path), metadata)
