"""Phân loại siêu dữ liệu chỉ dành cho laptop bảo thủ, đang chờ con người QA."""

import re
from dataclasses import dataclass
from src.data.loader import first_present


@dataclass(frozen=True)
class FilterDecision:
    include: bool
    reason: str


def classify_product(row: dict, rules: dict) -> FilterDecision:
    """Yêu cầu bằng chứng về danh mục và tiêu đề; không bao giờ kiểm tra văn bản hoặc xếp hạng review."""
    if not isinstance(row.get("parent_asin"), str) or not row["parent_asin"].strip():
        return FilterDecision(False, "missing_identifier")
    title, categories = row.get("title"), row.get("categories")
    if not isinstance(title, str) or not isinstance(categories, list) or any(not isinstance(value, str) for value in categories):
        return FilterDecision(False, "invalid_metadata_schema")
    if any(re.search(rules["category_exclude"], category, re.I) for category in categories):
        return FilterDecision(False, "excluded_category")
    if re.search(rules["title_exclude"], title, re.I):
        return FilterDecision(False, "accessory_or_ambiguous_title")
    category_match = any(value.casefold() in {c.casefold() for c in rules["laptop_categories"]} for value in categories)
    title_match = bool(re.search(rules["title_include"], title, re.I))
    if rules["require_category_and_title"]:
        include = category_match and title_match
    else:
        include = category_match or title_match
    return FilterDecision(include, "laptop_category_and_title" if include else "insufficient_laptop_evidence")


def parent_identifier(row: dict, aliases: list[str]) -> str:
    value = first_present(row, aliases, required=True)
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Product parent identifier must be a non-empty string")
    return value
