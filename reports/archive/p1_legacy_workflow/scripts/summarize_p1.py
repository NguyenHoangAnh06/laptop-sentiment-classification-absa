"""Tóm tắt các nghiên cứu nguồn nhỏ đã thực hiện; không suy ra số lượng kho văn bản."""

import csv
import argparse
import json
from pathlib import Path
from src.config import PROJECT_ROOT, load_config


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", nargs="+", default=["electronics_refactor", "cell_phones_refactor"])
    parser.add_argument("--output", default="p1_feasibility_small")
    args = parser.parse_args()
    for name in [*args.runs, args.output]:
        if not name or Path(name).name != name or name in {".", ".."}:
            parser.error("Run/output names must be simple file stems")
    tables = PROJECT_ROOT / "reports" / "tables"
    reports = [json.loads((tables / f"{name}.json").read_text(encoding="utf-8")) for name in args.runs]
    rows = [{"source": report["source"], "group": group, "coverage_complete": report["source_coverage_complete"], **metrics}
            for report in reports for group, metrics in report["groups"].items()]
    columns = ["source", "group", "coverage_complete", "candidate_products", "matched_reviews", "valid_reviews", "unique_products_with_reviews",
               "average_review_length_words", "duplicate_percentage", "rating_distribution", "language_distribution", "aspect_coverage_estimate",
               "short_review_percentage", "known_brands", "brand_missing_reviews", "clean_english_reviews", "near_duplicate_percentage", "filter_validation"]
    with (tables / f"{args.output}.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(row[key]) if isinstance(row[key], dict) else row[key] for key in columns})
    payload = {"scope": "small non-representative source snapshots; no cross-source deduplication claim",
               "observations": rows, "target_clean_reviews": load_config("data")["target_clean_reviews"],
               "capacity_clean_english": "NOT_MEASURED"}
    (tables / f"{args.output}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
