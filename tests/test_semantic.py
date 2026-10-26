"""Fixtures tổng hợp chỉ kiểm tra hợp đồng; không phải bằng chứng sentiment."""

import numpy as np
import pandas as pd
import pytest

from src.preprocessing.semantic import canonical_text, embedding_columns, ordered_digest, validate_matrix


def test_canonical_minimal_missing_negation():
    frame = pd.DataFrame({'review_title': [' Not good! ', None, 'Title only'],
                          'text': ['I do NOT like it...', 'body only', pd.NA], 'rating': [5, 1, 2]})
    assert canonical_text(frame) == ['Not good!\nI do NOT like it...', 'body only', 'Title only']
    changed = frame.assign(rating=3, review_id='secret', parent_asin='secret', label_id=2)
    assert canonical_text(changed) == canonical_text(frame)


def test_empty_or_unsupported_text_rejected():
    with pytest.raises(ValueError):
        canonical_text(pd.DataFrame({'review_title': [None], 'text': [' ']}))
    with pytest.raises(ValueError):
        canonical_text(pd.DataFrame({'review_title': ['a'], 'text': ['b'], 'language': ['vi']}))


@pytest.mark.parametrize('column', ['rating', 'stars', 'score', 'proxy_label', 'sentiment_label',
    'target', 'review_id', 'source_line', 'user_id', 'asin', 'parent_asin', 'label_id',
    'sentiment', 'verified_purchase', 'helpful_vote', 'text_length'])
def test_forbidden_features_fail(column):
    with pytest.raises(ValueError):
        validate_matrix(np.ones((2, 3), dtype='float32'), rows=2, dimension=3,
                        feature_columns=embedding_columns(3) + [column])


@pytest.mark.parametrize('value', [float('nan'), float('inf'), 0.])
def test_invalid_embedding(value):
    with pytest.raises(ValueError):
        validate_matrix(np.full((2, 3), value, dtype='float32'), rows=2, dimension=3,
                        feature_columns=embedding_columns(3))


def test_shape_dtype_order():
    matrix = np.ones((2, 3), dtype='float32')
    assert validate_matrix(matrix, rows=2, dimension=3, feature_columns=embedding_columns(3))['finite']
    with pytest.raises(ValueError):
        validate_matrix(matrix, rows=3, dimension=3, feature_columns=embedding_columns(3))
    assert ordered_digest(['a', 'b']) != ordered_digest(['b', 'a'])
