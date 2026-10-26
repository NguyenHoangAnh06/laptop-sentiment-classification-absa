"""Tải cài đặt dự án độc lập với thư mục làm việc hiện tại."""

from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_config(name: str, root: Path = PROJECT_ROOT) -> dict[str, Any]:
    """Đọc cấu hình YAML có tên; từ chối đường dẫn và tài liệu không hợp lệ."""
    if name not in {"data", "model", "language", "acquisition", "feasibility"}:
        raise ValueError(f"Unknown configuration: {name}")
    with (root / "configs" / f"{name}.yaml").open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    if not isinstance(config, dict):
        raise ValueError(f"Configuration {name} must be a mapping")
    return config


def dataset_path(key: str, root: Path = PROJECT_ROOT) -> Path:
    """Giải quyết đường dẫn dataset/artifact được định cấu hình đối với thư mục gốc của dự án."""
    return root / load_config("data", root)["paths"][key]
