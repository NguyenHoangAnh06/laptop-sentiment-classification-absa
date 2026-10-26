"""Đánh giá con người phạm vi gán nhãn so với đã cố định, các quyết định đường ống riêng biệt."""

import argparse
import json
from pathlib import Path

from src.data.independent_qa import evaluate_independent_qa, write_evaluation


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kit-dir", type=Path, required=True)
    parser.add_argument("--product-annotations", type=Path)
    parser.add_argument("--review-annotations", type=Path)
    parser.add_argument("--annotator", required=True, help="Tên hoặc bút danh con người")
    parser.add_argument("--confirm-independent-human", action="store_true",
                        help="Xác nhận con người verification/approval; tiết lộ riêng hỗ trợ AI")
    parser.add_argument("--ai-assisted-review", action="store_true",
                        help="Ghi lại xác minh con người sau khi có đề xuất AI; không yêu cầu gán nhãn bị mù hoàn toàn")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.output_dir.exists():
        parser.error("Use a new evaluation directory")
    result = evaluate_independent_qa(args.kit_dir, {
        "product": args.product_annotations or args.kit_dir / "product_annotation.csv",
        "review": args.review_annotations or args.kit_dir / "review_annotation.csv"},
        annotator=args.annotator, independent_human=args.confirm_independent_human,
        ai_assisted_review=args.ai_assisted_review)
    write_evaluation(result, args.output_dir)
    print(json.dumps({"status": result["status"], "pending_or_uncertain": result["pending_or_uncertain"],
                      "review_weighted_estimates": result["review_weighted_estimates"]}, indent=2))


if __name__ == "__main__":
    main()
