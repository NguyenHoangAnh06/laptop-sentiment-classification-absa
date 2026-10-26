"""Kiểm tra sản phẩm QA nhãn mà không sửa đổi chúng hoặc suy ra tổng thể độ bao phủ (recall)."""

import csv
from collections import Counter, defaultdict
from pathlib import Path

LABELS = {"true": True, "yes": True, "false": False, "no": False, "": None, "unsure": None}
PROVENANCES = {"unspecified", "ai_assisted_user_approved", "independent_human_verified"}


def read_qa(path: Path, label_column: str) -> list[dict]:
    """Từ chối CSV không đúng định dạng, cột không rõ ràng, ID trùng lặp và nhãn không hợp lệ."""
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, strict=True)
        fields = reader.fieldnames or []
        required = {"parent_asin", "rule_include", label_column, "human_notes"}
        if len(fields) != len(set(fields)) or not required.issubset(fields):
            raise ValueError("QA CSV missing or duplicate required fields")
        try:
            rows = list(reader)
        except csv.Error as exc:
            raise ValueError("Malformed QA CSV") from exc
    if not rows or any(None in row or any(v is None for v in row.values()) for row in rows):
        raise ValueError("QA CSV empty or contains malformed rows")
    identifiers = [row["parent_asin"].strip() for row in rows]
    if any(not value for value in identifiers) or len(set(identifiers)) != len(rows):
        raise ValueError("QA sample contains missing or duplicate product IDs")
    for row in rows:
        if row["rule_include"].strip().lower() not in {"true", "false"}:
            raise ValueError("rule_include must be True or False")
        if row[label_column].strip().lower() not in LABELS:
            raise ValueError(f"{label_column} must be True/False, yes/no, unsure or blank")
    return rows


def _rates(counts: Counter) -> dict:
    included = counts["true_positive"] + counts["false_positive"]
    excluded = counts["false_negative"] + counts["true_negative"]
    pending = counts["pending"]
    return {"rows": included + excluded + pending, "labeled_rows": included + excluded,
            "confusion_matrix": {key: counts[key] for key in
                                 ("true_positive", "false_positive", "false_negative", "true_negative")},
            "included_labeled_rows": included, "excluded_labeled_rows": excluded,
            "sample_precision": counts["true_positive"] / included if included else None,
            "false_positive_fraction_in_included": counts["false_positive"] / included if included else None,
            "false_negative_fraction_in_excluded": counts["false_negative"] / excluded if excluded else None,
            "pending_or_unsure": pending}


def validate_filter_qa(path: Path, minimum_included: int = 50, threshold: float = 0.95,
                       label_column: str = "human_is_laptop", *,
                       label_provenance: str = "unspecified") -> dict:
    """Báo cáo thống nhất mẫu phân tầng; phải khai báo xuất xứ rõ ràng."""
    if minimum_included < 1 or not 0 <= threshold <= 1 or label_provenance not in PROVENANCES:
        raise ValueError("Invalid QA criteria or label provenance")
    rows = read_qa(path, label_column)
    counts, strata, labels, mismatches = Counter(), defaultdict(Counter), Counter(), []
    accepted = 0
    for row in rows:
        decision = row["rule_include"].strip().lower() == "true"
        accepted += decision
        label = LABELS[row[label_column].strip().lower()]
        labels["pending" if label is None else "true" if label else "false"] += 1
        key = "pending" if label is None else (
            "true_positive" if decision and label else "false_positive" if decision else
            "false_negative" if label else "true_negative")
        counts[key] += 1
        strata[row.get("stratum", "unspecified")][key] += 1
        if label is not None and label != decision:
            mismatches.append({**row, "error_type": key})
    rates = _rates(counts)
    precision = rates["sample_precision"] if counts["pending"] == 0 else None
    passed = counts["pending"] == 0 and accepted >= minimum_included and precision is not None and precision >= threshold
    status = ("user_approved_sample" if label_provenance == "ai_assisted_user_approved" else "validated_sample") if passed else "unvalidated"
    return {"status": status, "label_provenance": label_provenance,
            "independent_human_verified": label_provenance == "independent_human_verified",
            "sample_precision_criterion_passed": passed, **rates,
            "label_counts": {key: labels[key] for key in ("true", "false", "pending")},
            "included_sample": accepted, "observed_precision": precision,
            "minimum_included": minimum_included, "required_precision": threshold,
            "excluded_sample_human_laptops": counts["false_negative"],
            "false_positives_in_included_sample": counts["false_positive"] if not counts["pending"] else None,
            "strata": {key: _rates(value) for key, value in strata.items()},
            "misclassified_products": mismatches,
            "population_recall": "NOT_MEASURED", "population_accuracy": "NOT_MEASURED",
            "note": "Stratified sample agreement only; AI-assisted user approval is not independent human gold. Excluded error fraction uses excluded labeled rows, not all actual laptops."}


def validate_product_qa(path: Path, minimum_included: int = 50, threshold: float = 0.95,
                        *, label_provenance: str = "unspecified") -> dict:
    """Kiểm tra QA khảo sát chỉ dành cho laptop; không bao giờ yêu cầu xác minh độc lập theo mặc định."""
    rows = read_qa(path, "human_is_target_product")
    if {row.get("group") for row in rows} != {"laptop"}:
        raise ValueError("QA file must describe the laptop target group")
    result = validate_filter_qa(path, minimum_included, threshold, "human_is_target_product",
                                label_provenance=label_provenance)
    result["group"] = "laptop"
    result["false_negatives_in_excluded_sample"] = result.pop("excluded_sample_human_laptops")
    return result
