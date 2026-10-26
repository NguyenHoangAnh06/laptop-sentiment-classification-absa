"""Chạy từ gốc dự án: python -m scripts.acquire_p1."""

import argparse
import json
from src.config import dataset_path, load_config
from src.data.acquisition import acquire


def main() -> None:
    parser = argparse.ArgumentParser(description="Có được ảnh chụp nhanh nguồn P1 thực có giới hạn")
    parser.add_argument("--source", choices=["metadata", "reviews", "trial"], required=True)
    parser.add_argument("--full", action="store_true", help="Tải xuống tệp Điện tử nén gốc; yêu cầu ủy quyền tải xuống lớn")
    parser.add_argument("--category", choices=["Electronics"], default="Electronics")
    parser.add_argument("--allow-large-download", action="store_true", help="Ủy quyền rõ ràng để tải xuống đầy đủ")
    args = parser.parse_args()
    config = load_config("acquisition")
    feasibility = load_config("feasibility")
    if args.full and not args.allow_large_download:
        parser.error("Full download requires --allow-large-download after user authorization")
    if args.source == "trial":
        if args.full:
            parser.error("--full is only for Amazon metadata/reviews")
        result = acquire(config["semeval"]["trial_url"], dataset_path("semeval_raw") / "laptops-trial.xml", max_bytes=2_000_000)
    else:
        settings = config["amazon"]
        url = feasibility["sources"][args.category][f"{args.source}_url"]
        if args.full:
            filename = f"meta_{args.category}.jsonl.gz" if args.source == "metadata" else f"{args.category}.jsonl.gz"
            result = acquire(url, dataset_path("amazon_raw") / filename,
                             max_bytes=settings["full_download_max_bytes"][args.source],
                             max_seconds=settings["full_download_max_seconds_per_file"][args.source])
        else:
            limit = settings[f"{args.source}_limit"]
            filename = f"{args.source}_prefix_{limit}.jsonl"
            max_bytes, max_seconds = settings["max_uncompressed_bytes_per_file"], settings["max_seconds_per_file"]
            result = acquire(url, dataset_path("amazon_raw") / filename,
                             limit=limit, max_bytes=max_bytes, max_seconds=max_seconds)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
