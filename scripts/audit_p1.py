"""siêu dữ liệu-điểm vào khảo sát đầu tiên; kiểm tra tiền tố ban đầu là chẩn đoán kế thừa rõ ràng."""

import csv
import json
from collections import Counter
from pathlib import Path

from src.config import PROJECT_ROOT, dataset_path, load_config
from src.data.acquisition import manifest_path, sha256_file
from src.data.laptop_filter import classify_product, parent_identifier
from src.data.loader import first_present, iter_jsonl
from src.data.semeval import parse_semeval
from src.data.validation import SchemaProfile, deterministic_sample, sample_reviews


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def audit_legacy_prefix() -> None:
    config, data = load_config("acquisition"), load_config("data")
    amazon, schema, rules = config["amazon"], config["schema"], config["filter"]
    meta_path = dataset_path("amazon_raw") / f"metadata_prefix_{amazon['metadata_limit']}.jsonl"
    reviews_path = dataset_path("amazon_raw") / f"reviews_prefix_{amazon['reviews_limit']}.jsonl"
    if (amazon['metadata_limit'] > 20000 or amazon['reviews_limit'] > 100000
            or meta_path.stat().st_size + reviews_path.stat().st_size > 160_000_000):
        raise ValueError("Legacy audit is limited to the original small snapshots; use metadata-first survey")
    manifests = {}
    for name, path in (("metadata", meta_path), ("reviews", reviews_path)):
        manifest = json.loads(manifest_path(path).read_text(encoding="utf-8"))
        if sha256_file(path) != manifest["sha256"]:
            raise ValueError(f"Raw checksum mismatch: {name}")
        manifests[name] = manifest
    metadata_profile, review_profile = SchemaProfile(), SchemaProfile()
    all_ids, products, qa = set(), {}, []
    decisions, counters = Counter(), Counter()
    for line, row in iter_jsonl(meta_path):
        metadata_profile.add(row)
        try:
            identifier = parent_identifier(row, schema["metadata_id"])
        except ValueError:
            counters["invalid_metadata_identifier"] += 1
            continue
        if identifier in all_ids:
            raise ValueError(f"Duplicate metadata parent_asin: {identifier}; resolve before joining")
        all_ids.add(identifier)
        decision = classify_product(row, rules)
        decisions[decision.reason] += 1
        details = row.get("details")
        if isinstance(details, str):
            try:
                details = json.loads(details)
            except json.JSONDecodeError:
                details = {}
        product = {"parent_asin": identifier, "title": row.get("title"), "categories": row.get("categories"),
                   "brand": details.get("Brand") if isinstance(details, dict) else None,
                   "store": row.get("store"), "source_line": line}
        if decision.include:
            products[identifier] = product
        qa.append({**product, "rule_include": decision.include, "rule_reason": decision.reason})
    filtered, rating_counts = [], Counter()
    source_hash = manifests["reviews"]["sha256"]
    for line, row in iter_jsonl(reviews_path):
        review_profile.add(row)
        try:
            identifier = parent_identifier(row, schema["review_parent_id"])
        except ValueError:
            counters["invalid_review_identifier"] += 1
            continue
        if identifier not in all_ids:
            counters["unmatched_metadata"] += 1
            continue
        counters["joined_reviews"] += 1
        if identifier not in products:
            counters["matched_non_laptop"] += 1
            continue
        # Xác thực các trường ranh giới nhưng giữ nguyên text/labels/duplicates cho P2.
        text = first_present(row, schema["review_text"])
        rating = first_present(row, schema["review_rating"])
        if isinstance(rating, bool) or not isinstance(rating, (int, float)) or rating not in (1, 2, 3, 4, 5):
            counters["candidate_invalid_rating"] += 1
            continue
        if not isinstance(text, str):
            counters["candidate_invalid_text_type"] += 1
            continue
        rating_counts[str(int(rating))] += 1
        filtered.append({"review_id": f"amazon2023:{source_hash}:{line}", "source_line": line,
                         "parent_asin": identifier, "asin": row.get("asin"), "text": text,
                         "user_id": row.get("user_id"),
                         "review_title": row.get("title"), "rating": int(rating),
                         "timestamp": first_present(row, schema["review_timestamp"]),
                         "helpful_vote": first_present(row, schema["review_helpful"]),
                         "verified_purchase": row.get("verified_purchase"),
                         "product_title": products[identifier]["title"], "brand": products[identifier]["brand"]})
    assert review_profile.rows == sum(counters[key] for key in ("invalid_review_identifier", "unmatched_metadata", "joined_reviews"))
    assert counters["joined_reviews"] == counters["matched_non_laptop"] + len(filtered) + counters["candidate_invalid_rating"] + counters["candidate_invalid_text_type"]
    sampled = sample_reviews(filtered, data["target_clean_reviews"], data["seed"])
    interim = dataset_path("interim")
    interim.mkdir(parents=True, exist_ok=True)
    for filename, rows in (("amazon_laptop_candidates.jsonl", filtered), ("amazon_laptop_sample.jsonl", sampled)):
        with (interim / filename).open("w", encoding="utf-8", newline="\n") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    qa_sample = []
    for included in (True, False):
        qa_sample.extend(deterministic_sample((row for row in qa if row["rule_include"] == included), config["qa"]["sample_size_per_decision"], data["seed"]))
    qa_path = dataset_path("manual") / "laptop_filter_qa.csv"
    qa_path.parent.mkdir(parents=True, exist_ok=True)
    # Giữ nguyên mọi con người nhãn gán khi chạy lại; buộc một tập tin mới nếu thành viên thay đổi.
    fields = ["parent_asin", "title", "categories", "brand", "store", "source_line", "rule_include", "rule_reason", "human_is_laptop", "human_notes"]
    expected_ids = [row["parent_asin"] for row in qa_sample]
    if qa_path.exists():
        with qa_path.open(encoding="utf-8-sig", newline="") as handle:
            existing = list(csv.DictReader(handle))
        if [row["parent_asin"] for row in existing] != expected_ids:
            raise ValueError("Existing QA sample differs; preserve annotations and use a new path")
    else:
        with qa_path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for row in qa_sample:
                writer.writerow({**row, "categories": json.dumps(row["categories"], ensure_ascii=False), "human_is_laptop": "", "human_notes": ""})
    semeval = {}
    for filename, split in (("laptops-trial.xml", "trial"), ("Laptop_Train_v2.xml", "train"), ("Laptops_Test_Gold.xml", "test")):
        path = dataset_path("semeval_raw") / filename
        if not path.exists():
            semeval[split] = {"status": "missing"}
            continue
        parsed = parse_semeval(path, split)
        polarities = Counter(aspect["original_polarity"] for row in parsed for aspect in row["aspects"])
        semeval[split] = {"status": "audited", "sentences": len(parsed), "aspects": sum(polarities.values()), "polarities": dict(polarities), "sha256": sha256_file(path)}
        write_json(interim / f"semeval_{split}_audit.json", parsed)
    report = {
        "scope": "bounded_source_prefix_not_full_electronics_pool", "seed": data["seed"],
        "filter_version": rules["version"], "filter_validation": "unvalidated",
        "source_manifests": manifests,
        "metadata_schema": metadata_profile.to_dict(), "review_schema": review_profile.to_dict(),
        "join_key": "parent_asin", "filter_decisions": dict(decisions), "join_counts": dict(counters),
        "candidate_products": len(products), "candidate_reviews": len(filtered),
        "products_with_candidate_reviews": len({row["parent_asin"] for row in filtered}),
        "rating_counts": {str(rating): rating_counts[str(rating)] for rating in range(1, 6)},
        "rating_percentages": {str(rating): (100 * rating_counts[str(rating)] / len(filtered) if filtered else None) for rating in range(1, 6)},
        "sample_reviews": len(sampled), "sample_products": len({row["parent_asin"] for row in sampled}),
        "sample_known_brands": len({row["brand"] for row in sampled if row["brand"]}),
        "clean_size_estimate": None, "clean_size_estimate_reason": "P2 cleaning and human filter QA not performed; prefix cannot estimate full pool",
        "human_qa_rows": len(qa_sample), "semeval": semeval,
    }
    write_json(PROJECT_ROOT / "reports" / "tables" / "p1_audit.json", report)
    print(json.dumps({key: report[key] for key in ("candidate_products", "candidate_reviews", "products_with_candidate_reviews", "rating_counts", "semeval")}, indent=2))


if __name__ == "__main__":
    import sys
    if sys.argv[1:] == ["--legacy-prefix"]:
        audit_legacy_prefix()
    else:
        from scripts.survey_p1 import main
        main()
