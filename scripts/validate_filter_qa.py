"""Xác thực CSV con người QA đã hoàn thành; không bao giờ thay đổi nhãn hoặc bật bộ lọc."""

import json
import argparse
from pathlib import Path
from src.config import dataset_path, load_config
from src.data.filter_qa import PROVENANCES, validate_filter_qa, validate_product_qa


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", type=Path, help="CSV QA nhóm mới; không có đối số này, hãy sử dụng laptop mô hình cơ sở QA gốc")
    parser.add_argument("--label-provenance", choices=sorted(PROVENANCES), default="unspecified")
    parser.add_argument("--output", type=Path, help="Báo cáo JSON mới; từ chối ghi đè lên các tập tin hiện có")
    args = parser.parse_args()
    config = load_config("acquisition")["qa"]
    validate = validate_product_qa if args.path else validate_filter_qa
    result = validate(args.path or dataset_path("manual") / "laptop_filter_qa.csv",
                                config["sample_size_per_decision"], config["required_precision"],
                                label_provenance=args.label_provenance)
    if args.output:
        with args.output.open("x", encoding="utf-8") as handle:
            handle.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, indent=2))
