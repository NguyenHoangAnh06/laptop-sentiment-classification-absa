"""Kiểm tra phiên bản TabPFN bằng API thật, không download checkpoint."""

from pathlib import Path

import pytest

from src.sentiment.tabpfn_versions import make_tabpfn, version_resolution


def test_versions_resolve_distinct_checkpoints():
    paths = version_resolution()
    assert len(paths) == 2
    assert len({Path(p).name for p in paths.values()}) == 2
    assert 'v3' in Path(paths['E03_tabpfn_v3_embedding']).name
    assert '3.5' in Path(paths['E04_tabpfn_v35_embedding']).name


@pytest.mark.parametrize('experiment,kwargs', [
    ('tabpfn', {}), ('E03_tabpfn_v3_embedding', {'model_path': 'auto'})])
def test_ambiguous_version_rejected(experiment, kwargs):
    with pytest.raises(ValueError):
        make_tabpfn(experiment, **kwargs)
