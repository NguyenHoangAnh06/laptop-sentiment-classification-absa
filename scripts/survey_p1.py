"""siêu dữ liệu-tính khả thi đầu tiên; đầu dò là mặc định và không bao giờ trở thành bản quét lớn."""

import argparse
import json
from pathlib import Path

from src.config import PROJECT_ROOT, dataset_path, load_config
from src.data.feasibility import run_feasibility


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", choices=list(load_config("feasibility")["sources"]), required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--reviews", type=Path)
    parser.add_argument("--metadata-only", action="store_true", help="Xác thực siêu dữ liệu coverage/index trước khi tải xuống review")
    parser.add_argument("--groups", nargs="+", choices=["laptop"], help="Chỉ laptop; được giữ lại để tương thích với CLI")
    parser.add_argument("--run", required=True, help="Tên thư mục chạy mới, ví dụ: electronics_probe_v2")
    parser.add_argument("--mode", choices=["probe", "scan"], default="probe")
    parser.add_argument("--allow-large-scan", action="store_true")
    args = parser.parse_args()
    if not args.metadata_only and args.reviews is None:
        parser.error("--reviews required unless --metadata-only")
    if not args.run or Path(args.run).name != args.run or args.run in {".", ".."}:
        parser.error("--run must be a simple directory name")
    config = load_config("feasibility")
    if args.groups:
        config["groups"] = list(dict.fromkeys(args.groups))
    result = run_feasibility(args.metadata, args.reviews, dataset_path("interim") / "feasibility" / args.run,
                             dataset_path("manual") / "feasibility", config, load_config("acquisition"),
                             source=args.source, mode=args.mode, seed=load_config("data")["seed"], allow_large_scan=args.allow_large_scan,
                             metadata_only=args.metadata_only)
    tables = PROJECT_ROOT / "reports" / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    (tables / f"{args.run}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.metadata_only:
        print(json.dumps(result, indent=2))
        return
    print(json.dumps({"source": args.source, "coverage_complete": result["source_coverage_complete"],
                      "groups": {g: {k: values[k] for k in ("candidate_products", "matched_reviews", "valid_reviews", "unique_products_with_reviews")} for g, values in result["groups"].items()},
                      "resources": result["resources"]}, indent=2))


if __name__ == "__main__":
    main()
