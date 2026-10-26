"""Kiểm tra lấy mẫu tài nguyên train-only và tính xác định, không inference nặng."""

import numpy as np
import pytest

from scripts.assess_tabpfn import stratified_ids
from src.evaluation.redaction import safe_error


def test_exception_never_records_token_or_url(monkeypatch):
    monkeypatch.setenv('TABPFN_TOKEN', 'fixture-secret-do-not-persist')
    text = safe_error(ValueError('fixture-secret-do-not-persist https://example.test/?token=secret'))
    assert 'fixture-secret' not in text and 'https://' not in text and 'token=secret' not in text


def test_resource_sampling_is_deterministic_and_stratified():
    labels = np.repeat([0, 1, 2], [300, 100, 600])
    first = stratified_ids(labels, 500)
    np.testing.assert_array_equal(first, stratified_ids(labels, 500))
    assert len(set(first)) == 500
    np.testing.assert_array_equal(np.bincount(labels[first]), [150, 50, 300])
    np.testing.assert_array_equal(stratified_ids(labels, 1000), np.arange(1000))


@pytest.mark.parametrize('size', [0, -1, 1001])
def test_resource_sampling_invalid_size(size):
    with pytest.raises(ValueError):
        stratified_ids(np.repeat([0, 1, 2], [300, 100, 600]), size)
