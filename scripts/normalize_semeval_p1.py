"""Chuyển đổi XML SemEval laptop do người dùng cung cấp thành JSONL được kiểm tra, không mất dữ liệu."""

import argparse
import json
from pathlib import Path

from src.data.semeval import normalize_semeval


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", type=Path, default=Path("data/raw/semeval/Laptop_Train_v2.xml"))
    parser.add_argument("--test", type=Path, default=Path("data/raw/semeval/Laptops_Test_Gold.xml"))
    parser.add_argument("--output-dir", type=Path, default=Path("data/interim/semeval"))
    parser.add_argument("--report", type=Path, default=Path("reports/tables/p1_semeval_normalization.json"))
    args = parser.parse_args()
    if args.report.exists():
        parser.error("Report already exists; choose a new --report for a rerun")
    report = normalize_semeval({"train": args.train, "test": args.test}, args.output_dir)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(json.dumps({s: {k: v for k, v in r.items() if k not in {"input", "output", "duplicate_text_groups", "diagnostics"}} for s, r in report["splits"].items()}, indent=2))


if __name__ == "__main__":
    main()
