"""Chọn phiên bản TabPFN tường minh; không tải checkpoint lúc import."""

from pathlib import Path
import importlib.metadata

VERSIONS = {'E03_tabpfn_v3_embedding': 'V3', 'E04_tabpfn_v35_embedding': 'V3_5'}


def make_tabpfn(experiment: str, **overrides):
    """Từ chối default mơ hồ và override checkpoint khác với phiên bản yêu cầu."""
    if importlib.metadata.version('tabpfn') != '9.2.0':
        raise ValueError('Benchmark này yêu cầu tabpfn==9.2.0')
    from tabpfn import TabPFNClassifier
    from tabpfn.constants import ModelVersion

    if experiment not in VERSIONS or 'model_path' in overrides:
        raise ValueError('Cần experiment TabPFN tường minh; không override model_path')
    version = getattr(ModelVersion, VERSIONS[experiment])
    return TabPFNClassifier.create_default_for_version(version, **overrides)


def version_resolution() -> dict[str, str]:
    """Xác minh hai phiên bản thực sự resolve sang hai checkpoint riêng biệt."""
    paths = {key: str(make_tabpfn(key, device='cpu', n_estimators=1).model_path)
             for key in VERSIONS}
    if len({Path(p).name for p in paths.values()}) != len(VERSIONS):
        raise ValueError('TabPFN-3 và TabPFN-3.5 resolve trùng checkpoint')
    from tabpfn.model_loading import resolve_model_version
    for experiment, path in paths.items():
        if resolve_model_version(Path(path)).name != VERSIONS[experiment]:
            raise ValueError('Phiên bản suy từ checkpoint không khớp phiên bản yêu cầu')
    return paths
