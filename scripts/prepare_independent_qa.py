"""Chuẩn bị các tệp P1 gán nhãn mù mới từ một lần chạy Điện tử hoàn chỉnh hiện có."""

import argparse
import json
from pathlib import Path

from src.config import dataset_path, load_config
from src.data.independent_qa import prepare_independent_qa


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--raw-dir", type=Path, default=dataset_path("amazon_raw"))
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=load_config("data")["seed"])
    args = parser.parse_args()
    result = prepare_independent_qa(args.run_dir, args.raw_dir, args.output_dir,
                                    load_config("acquisition"), load_config("feasibility")["limits"], seed=args.seed)
    print(json.dumps({"status": result["status"], "populations": result["populations"],
                      "samples": result["samples"], "resources": result["resources"]}, indent=2))


if __name__ == "__main__":
    main()
