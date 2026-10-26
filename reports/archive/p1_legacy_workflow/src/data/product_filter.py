"""Bộ lọc nhóm có thể định cấu hình chỉ dành cho tính khả thi; laptop mô hình cơ sở không thay đổi."""

import re
from src.data.laptop_filter import FilterDecision, classify_product


def classify_group(row: dict, group: str, rules: dict, laptop_rules: dict) -> FilterDecision:
    """Yêu cầu cả bằng chứng về danh mục và tiêu đề sản phẩm, độc lập với review."""
    if group == "laptop":
        return classify_product(row, laptop_rules)
    if group not in rules:
        raise ValueError(f"No product rule for {group}")
    if not isinstance(row.get("parent_asin"), str) or not row["parent_asin"].strip():
        return FilterDecision(False, "missing_identifier")
    title, categories = row.get("title"), row.get("categories")
    if not isinstance(title, str) or not isinstance(categories, list) or any(not isinstance(c, str) for c in categories):
        return FilterDecision(False, "invalid_metadata_schema")
    rule = rules[group]
    # Khớp các nút danh mục, không phải tổ tiên danh mục chung '... & Phụ kiện'.
    leaves = [c for c in categories if " & Accessories" not in c]
    if any(re.search(rule["category_exclude"], c, re.I) for c in leaves):
        return FilterDecision(False, "excluded_category")
    if re.search(rule["title_exclude"], title, re.I):
        return FilterDecision(False, "accessory_or_ambiguous_title")
    category_match = any(c.casefold() in {v.casefold() for v in rule["categories"]} for c in categories)
    if category_match and re.search(rule["title_include"], title, re.I):
        return FilterDecision(True, "category_and_title")
    return FilterDecision(False, "insufficient_group_evidence")


def classify_groups(row: dict, config: dict, laptop_rules: dict) -> dict[str, FilterDecision]:
    decisions = {group: classify_group(row, group, config["product_rules"], laptop_rules) for group in config["groups"]}
    categories = row.get("categories", [])
    category_groups = 0
    if isinstance(categories, list) and all(isinstance(c, str) for c in categories):
        # Các biện pháp bảo vệ chống sự mơ hồ cũng được áp dụng khi chỉ chọn một nhóm đầu ra.
        for group in dict.fromkeys(["laptop", *config["product_rules"]]):
            allowed = laptop_rules["laptop_categories"] if group == "laptop" else config["product_rules"][group]["categories"]
            category_groups += any(c.casefold() in {v.casefold() for v in allowed} for c in categories)
    if sum(d.include for d in decisions.values()) > 1 or category_groups > 1:
        return {group: FilterDecision(False, "ambiguous_multiple_groups") for group in decisions}
    return decisions
