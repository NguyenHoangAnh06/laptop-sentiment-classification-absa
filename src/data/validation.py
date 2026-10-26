"""Hồ sơ lược đồ được quan sát và lấy mẫu thăm dò có thể tái tạo."""

import hashlib
import json
from collections import Counter, defaultdict
from collections.abc import Iterable


class SchemaProfile:
    """Cấu hình các loại được quan sát và giá trị null/absent mà không giữ lại các hàng nguồn."""

    def __init__(self) -> None:
        self.rows = 0
        self.present = Counter()
        self.null = Counter()
        self.types = defaultdict(Counter)

    def add(self, row: dict) -> None:
        self.rows += 1
        for key, value in row.items():
            self.present[key] += 1
            self.null[key] += value is None
            self.types[key][type(value).__name__] += 1

    def to_dict(self) -> dict:
        return {"rows": self.rows, "fields": {
            key: {"types": dict(self.types[key]), "absent": self.rows - self.present[key], "null": self.null[key]}
            for key in sorted(self.present)
        }}


def stable_key(value: dict, seed: int) -> str:
    """Sắp xếp theo hàm băm nội dung do hạt giống ngẫu nhiên kiểm soát, độc lập với ngẫu nhiên hàm băm Python."""
    text = json.dumps(value, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(f"{seed}:{text}".encode("utf-8")).hexdigest()


def deterministic_sample(rows: Iterable[dict], size: int, seed: int) -> list[dict]:
    if size < 0:
        raise ValueError("Sample size must be nonnegative")
    return sorted(rows, key=lambda row: stable_key(row, seed))[:size]


def sample_reviews(rows: list[dict], size: int, seed: int) -> list[dict]:
    """Tầng đánh giá theo tỷ lệ; sản phẩm quay vòng bên trong mỗi tầng."""
    if size < 0:
        raise ValueError("Sample size must be nonnegative")
    target = min(size, len(rows))
    if target == 0:
        return []
    strata = defaultdict(list)
    for row in rows:
        strata[row["rating"]].append(row)
    quotas = {rating: int(target * len(values) / len(rows)) for rating, values in strata.items()}
    remainders = sorted(strata, key=lambda rating: (-(target * len(strata[rating]) / len(rows) - quotas[rating]), rating))
    for rating in remainders[:target - sum(quotas.values())]:
        quotas[rating] += 1
    selected = []
    for rating in sorted(strata):
        products = defaultdict(list)
        for row in strata[rating]:
            products[row["parent_asin"]].append(row)
        for key in products:
            products[key] = sorted(products[key], key=lambda row: stable_key(row, seed), reverse=True)
        product_order = sorted(products, key=lambda key: stable_key({"parent_asin": key}, seed))
        remaining = quotas[rating]
        while remaining:
            for key in product_order:
                if products[key] and remaining:
                    selected.append(products[key].pop())
                    remaining -= 1
    return sorted(selected, key=lambda row: stable_key(row, seed))
