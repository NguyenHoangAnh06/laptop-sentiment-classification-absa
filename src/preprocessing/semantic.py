"""Hợp đồng văn bản/ma trận cho benchmark semantic, không chứa TF-IDF."""

import hashlib
import json
import re
import unicodedata

import numpy as np
import pandas as pd

TEXT_FIELDS = ('review_title', 'text')
TEXT_DEFINITION = 'NFC + whitespace collapse; review_title + newline + text; omit missing parts; v1'


def normalize_part(value: object) -> str:
    """Giữ chữ hoa, phủ định, dấu câu; null được biểu diễn bằng chuỗi rỗng."""
    if value is None or pd.isna(value):
        return ''
    if not isinstance(value, str):
        raise ValueError('Title/body phải là chuỗi hoặc null')
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFC', value)).strip()


def canonical_text(frame: pd.DataFrame) -> list[str]:
    """Chỉ lấy hai cột văn bản được cho phép, không chuyển metadata thành text."""
    if not set(TEXT_FIELDS) <= set(frame.columns) or frame.empty:
        raise ValueError('Cần frame không rỗng với review_title và text')
    if 'language' in frame and not frame.language.eq('en').all():
        raise ValueError('Hiện chỉ hỗ trợ tiếng Anh')
    texts = ['\n'.join(p for p in (normalize_part(title), normalize_part(body)) if p)
             for title, body in frame.loc[:, TEXT_FIELDS].itertuples(index=False, name=None)]
    if any(not text for text in texts):
        raise ValueError('Title và body đều rỗng')
    return texts


def ordered_digest(values: list) -> str:
    """Băm theo thứ tự với ranh giới JSON, tránh xung đột do nối chuỗi."""
    return hashlib.sha256(json.dumps(values, ensure_ascii=False, separators=(',', ':')).encode('utf-8')).hexdigest()


def embedding_columns(dimension: int) -> list[str]:
    if dimension < 1:
        raise ValueError('Dimension phải dương')
    return [f'embedding_{i:04d}' for i in range(dimension)]


def validate_matrix(matrix: np.ndarray, *, rows: int, dimension: int,
                    feature_columns: list[str]) -> dict:
    """Fail closed với cột ngoài whitelist, kể cả ID/target/metadata."""
    if feature_columns != embedding_columns(dimension):
        raise ValueError('Feature ngoài embedding whitelist: có thể rò rỉ target/ID/metadata')
    if not isinstance(matrix, np.ndarray) or matrix.shape != (rows, dimension) or rows < 1:
        raise ValueError('Sai shape embedding')
    if matrix.dtype not in (np.dtype('float32'), np.dtype('float16')):
        raise ValueError('Embedding phải float32/float16')
    if not np.isfinite(matrix).all():
        raise ValueError('Embedding chứa NaN/Inf')
    norms = np.linalg.norm(matrix.astype(np.float32), axis=1)
    if (norms < 1e-8).any() or (norms > 1e4).any():
        raise ValueError('Embedding zero/abnormal norm')
    return {'shape': list(matrix.shape), 'dtype': str(matrix.dtype),
            'norm_min': float(norms.min()), 'norm_max': float(norms.max()), 'finite': True}
