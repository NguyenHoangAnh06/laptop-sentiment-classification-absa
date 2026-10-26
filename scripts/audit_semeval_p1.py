"""Kiểm tra các tệp XML SemEval laptop được ủy quyền cục bộ mà không cần tải xuống hoặc huấn luyện."""

import argparse
import json
from pathlib import Path

from src.config import dataset_path
from src.data.semeval import audit_semeval_splits


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    raw = dataset_path("semeval_raw")
    parser.add_argument("--train", type=Path, default=raw / "laptops-train.xml")
    parser.add_argument("--test", type=Path, default=raw / "laptops-test.xml")
    parser.add_argument("--trial", type=Path, default=raw / "laptops-trial.xml")
    parser.add_argument("--output", type=Path, required=True, help="Tệp JSON mới; không bao giờ ghi đè")
    args = parser.parse_args()
    report = audit_semeval_splits({"train": args.train, "test": args.test, "trial": args.trial})
    with args.output.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
