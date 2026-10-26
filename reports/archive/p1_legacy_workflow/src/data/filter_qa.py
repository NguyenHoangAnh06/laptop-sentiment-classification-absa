"""Xác thực bộ lọc thực sự con người nhãn mà không tạo nhãn gán."""

import csv
from pathlib import Path


def validate_filter_qa(path: Path, minimum_included: int = 50, threshold: float = 0.95,
                       label_column: str = "human_is_laptop") -> dict:
    """Chỉ trả lại mẫu độ chính xác dự đoán (precision) đã quan sát khi có con người nhãn gán được yêu cầu."""
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        required = {"parent_asin", "rule_include", label_column, "human_notes"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("QA CSV missing required fields")
        rows = list(reader)
    if not rows or len({row["parent_asin"] for row in rows}) != len(rows):
        raise ValueError("QA sample is empty or contains duplicate product IDs")
    pending, accepted, correct, rejected_laptops = 0, 0, 0, 0
    for row in rows:
        decision = row["rule_include"].strip().lower()
        if decision not in {"true", "false"}:
            raise ValueError("rule_include must be True or False")
        label = row[label_column].strip().lower()
        if label not in {"", "yes", "no", "unsure"}:
            raise ValueError(f"{label_column} must be yes, no, unsure or blank")
        if label in {"", "unsure"}:
            pending += 1
        if decision == "true":
            accepted += 1
            correct += label == "yes"
        elif label == "yes":
            rejected_laptops += 1
    precision = correct / accepted if accepted and pending == 0 else None
    return {"status": "validated_sample" if pending == 0 and accepted >= minimum_included and precision >= threshold else "unvalidated",
            "rows": len(rows), "pending_or_unsure": pending, "included_sample": accepted,
            "observed_precision": precision, "minimum_included": minimum_included,
            "required_precision": threshold, "excluded_sample_human_laptops": rejected_laptops,
            "false_positives_in_included_sample": accepted - correct if pending == 0 else None,
            "note": "Sample precision is not a population guarantee; source coverage remains separate."}


def validate_product_qa(path: Path, minimum_included: int = 50, threshold: float = 0.95) -> dict:
    """Xác thực một tệp QA khảo sát dành riêng cho nhóm; không bao giờ yêu cầu dân số độ bao phủ (recall)."""
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    groups = {row.get("group") for row in rows}
    if len(groups) != 1 or not groups.issubset({"laptop", "smartphone", "tablet"}):
        raise ValueError("QA file must describe one known target group")
    result = validate_filter_qa(path, minimum_included, threshold, "human_is_target_product")
    result["group"] = next(iter(groups))
    result["false_negatives_in_excluded_sample"] = result.pop("excluded_sample_human_laptops")
    result["population_recall"] = "NOT_MEASURED"
    return result
