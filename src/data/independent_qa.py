"""Chuẩn bị mù con người phạm vi QA; không bao giờ suy ra con người nhãn từ các quyết định mô hình."""

import csv
import gzip
import json
import random
import re
import time
from collections import Counter, defaultdict
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from src.data.acquisition import sha256_file
from src.data.feasibility import check_memory, process_memory, source_info
from src.data.laptop_filter import classify_product, parent_identifier
from src.data.loader import first_present, iter_jsonl, scan_jsonl, ScanStats
from src.data.survey import normalize_for_survey
from src.data.validation import stable_key

VERSION = "independent_domain_qa_v1"
HUMAN_COLUMNS = ["human_label", "human_evidence", "human_notes", "human_error_reason"]
PRODUCT_COLUMNS = ["annotation_id", "product_id", "title", "categories", "description",
                   "features", "details", "source_evidence", "product_url"] + HUMAN_COLUMNS
REVIEW_COLUMNS = ["annotation_id", "review_id", "product_id", "review_title", "review_text",
                  "title", "categories", "description", "features", "details",
                  "source_evidence", "product_url"] + HUMAN_COLUMNS
LABELS = {"laptop": True, "non_laptop": False, "uncertain": None, "": None}
ERROR_REASONS = {"", "accessory", "tablet_only", "desktop", "other_non_laptop",
                 "convertible_2in1", "model_only_title", "missing_laptop_category",
                 "misleading_title_category", "missing_metadata", "incorrect_metadata",
                 "linkage_problem", "insufficient_evidence", "other"}


def read_csv(path: Path) -> tuple[list[str], list[dict]]:
    """Trình đọc CSV nghiêm ngặt, bao gồm kiểm tra tiêu đề trùng lặp và độ rộng hàng."""
    try:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle, strict=True)
            columns = reader.fieldnames or []
            rows = list(reader)
    except csv.Error as exc:
        raise ValueError(f"Malformed CSV: {path}") from exc
    if not rows or len(set(columns)) != len(columns) or any(None in r or None in r.values() for r in rows):
        raise ValueError(f"Empty/malformed CSV or duplicate header: {path}")
    return columns, rows


def write_csv(path: Path, columns: list[str], rows: list[dict]) -> None:
    """Chỉ các tập tin mới; UTF-8 BOM cho phép Excel đọc Unicode chính xác."""
    with path.open("x", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def fixed_fingerprint(row: dict) -> str:
    return stable_key({k: v for k, v in row.items() if k not in HUMAN_COLUMNS}, 0)


class Reservoir:
    """Lấy mẫu thống nhất mà không cần thay thế từ luồng được xác định rõ ràng."""

    def __init__(self, size: int, seed: int):
        self.size, self.rng, self.count, self.rows = size, random.Random(seed), 0, []

    def add(self, row: dict) -> None:
        self.count += 1
        if len(self.rows) < self.size:
            self.rows.append(row)
        else:
            position = self.rng.randrange(self.count)
            if position < self.size:
                self.rows[position] = row


def metadata_fields(row: dict | None, evidence: dict) -> dict:
    """Giữ lại bằng chứng siêu dữ liệu; URL là gợi ý tra cứu, không phải bằng chứng trực tiếp được xác minh."""
    row = row or {}
    return {"title": row.get("title"), "categories": row.get("categories"),
            "description": row.get("description"), "features": row.get("features"),
            "details": row.get("details"), "source_evidence": evidence}


def _strings(row: dict, columns: list[str]) -> dict:
    return {key: "" if row.get(key) is None else json.dumps(row[key], ensure_ascii=False)
            if isinstance(row[key], (list, dict)) else str(row[key]) for key in columns}


def prepare_independent_qa(run: Path, raw_dir: Path, output: Path, acquisition: dict,
                           limits: dict, *, seed: int = 42, product_n: int = 150,
                           boundary_n: int = 50, review_n: int = 150,
                           diagnostic_n: int = 100) -> dict:
    """Lấy mẫu các khung KEEP và REJECT thô đã lưu mà không cần chạy lại khảo sát tính khả thi."""
    if min(product_n, review_n) < 1 or min(boundary_n, diagnostic_n) < 0:
        raise ValueError("Invalid sample sizes")
    if output.exists():
        raise FileExistsError("Use a new QA directory; never overwrite annotation")
    protected = [run.resolve(), raw_dir.resolve()]
    if any(output.resolve() == p or output.resolve() in p.parents or p in output.resolve().parents for p in protected):
        raise ValueError("QA output must be separate from source/run directories")
    started = time.monotonic()
    deadline = started + limits["max_scan_seconds"]
    report_path = run / "report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if report["source"] != "Electronics" or not report["source_coverage_complete"]:
        raise ValueError("Complete Electronics run required")
    paths = {kind: raw_dir / info["name"] for kind, info in report["inputs"].items()}
    inputs = {}
    for kind, path in paths.items():
        info = source_info(path)
        if (info["sha256"] != report["inputs"][kind]["sha256"] or not info["complete_source"]
                or info["manifest"]["source_url"] != acquisition["amazon"][f"{kind}_url"]):
            raise ValueError(f"Source snapshot/provenance mismatch: {kind}")
        inputs[kind] = {"path": path.as_posix(), "sha256": info["sha256"],
                        "bytes": path.stat().st_size, "manifest": info["manifest"]}
    for name in ("products.jsonl", "laptop_valid.jsonl"):
        if sha256_file(run / name) != report["output_sha256"][name]:
            raise ValueError(f"Saved run checksum mismatch: {name}")
    products = {}
    for _, row in iter_jsonl(run / "products.jsonl"):
        identifier = parent_identifier(row, acquisition["schema"]["metadata_id"])
        if identifier in products or not classify_product(row, acquisition["filter"]).include:
            raise ValueError("Duplicate product or current filter differs from saved KEEP")
        products[identifier] = row
    if len(products) != report["groups"]["laptop"]["candidate_products"]:
        raise ValueError("Product frame count mismatch")
    product_ids = random.Random(seed + 1).sample(sorted(products), min(product_n, len(products)))
    n_keep = report["groups"]["laptop"]["valid_reviews"]
    keep_indices = set(random.Random(seed + 2).sample(range(1, n_keep + 1), min(review_n, n_keep)))
    keep, diagnostics = [], Reservoir(diagnostic_n, seed + 3)
    valid_count = 0
    for index, row in iter_jsonl(run / "laptop_valid.jsonl"):
        valid_count += 1
        if index in keep_indices:
            keep.append(row)
        elif len(normalize_for_survey(row["text"]).split()) < 5 or re.search(r"\b(tablet|convertible|2.in.1|detachable)\b", row["product_title"], re.I):
            diagnostics.add(row)
        if index % 10000 == 0:
            check_memory(limits["max_process_working_set_bytes"])
            if time.monotonic() >= deadline:
                raise TimeoutError("QA preparation deadline exceeded")
    if valid_count != n_keep:
        raise ValueError("KEEP frame count mismatch")
    n_raw = report["review_scan"]["rows"]
    candidate_lines = random.Random(seed + 4).sample(range(1, n_raw + 1), min(n_raw, max(review_n * 3, review_n)))
    wanted = set(candidate_lines)
    raw_candidates = {}
    decoded_bytes = 0
    opener = gzip.open if paths["reviews"].suffix == ".gz" else open
    # Chỉ các dòng vật lý được chọn mới được giải mã JSON; tất cả các byte gzip được đọc cho CRC/EOF.
    with opener(paths["reviews"], "rb") as handle:
        for line, payload in enumerate(handle, 1):
            decoded_bytes += len(payload)
            if len(payload) > limits["max_record_bytes"] or decoded_bytes > limits["max_scan_read_bytes"]:
                raise ValueError("Raw review record/read budget exceeded")
            if line in wanted:
                raw_candidates[line] = json.loads(payload)
            if line % 1000000 == 0:
                check_memory(limits["max_process_working_set_bytes"])
                if time.monotonic() >= deadline:
                    raise TimeoutError("QA preparation deadline exceeded")
                print(f"QA selective review extraction: {line:,}/{n_raw:,}", flush=True)
    if line != n_raw or len(raw_candidates) != len(wanted):
        raise ValueError("Raw review count differs from saved snapshot")
    rejected = []
    for source_line in candidate_lines:
        row = raw_candidates[source_line]
        identifier = parent_identifier(row, acquisition["schema"]["review_parent_id"])
        if identifier not in products:
            rejected.append({"review_id": f"amazon2023:{inputs['reviews']['sha256']}:{source_line}",
                             "source_line": source_line, "parent_asin": identifier,
                             "text": first_present(row, acquisition["schema"]["review_text"]),
                             "review_title": first_present(row, acquisition["schema"]["review_title"])})
        if len(rejected) == review_n:
            break
    if len(rejected) < review_n:
        raise ValueError("Insufficient REJECT candidates; increase oversampling in a new version/run")
    review_groups = [("random_keep", keep, n_keep, True),
                     ("random_reject", rejected, report["join_counts"]["not_in_selected_metadata_index"], False),
                     ("diagnostic", diagnostics.rows, diagnostics.count, True)]
    needed = set(product_ids) | {r["parent_asin"] for _, rows, _, _ in review_groups for r in rows}
    enriched, boundary = {}, Reservoir(boundary_n, seed + 5)
    stats = ScanStats()
    for source_line, row in scan_jsonl(paths["metadata"], stats, max_rows=limits["scan_metadata_records"],
                                        max_bytes=limits["max_scan_read_bytes"] - decoded_bytes,
                                        deadline=deadline, max_record_bytes=limits["max_record_bytes"]):
        identifier = parent_identifier(row, acquisition["schema"]["metadata_id"])
        decision = classify_product(row, acquisition["filter"])
        if decision.include != (identifier in products):
            raise ValueError("Current filter and saved metadata selections differ; do not evaluate stale predictions")
        evidence = {"dataset": "Amazon Reviews 2023 Electronics", "metadata_file": paths["metadata"].as_posix(),
                    "metadata_sha256": inputs["metadata"]["sha256"], "metadata_line": source_line,
                    "join_key": "parent_asin", "external_url_status": "lookup_hint_not_verified"}
        compact = {"product_id": identifier, **metadata_fields(row, evidence)}
        if identifier in needed:
            if identifier in enriched:
                raise ValueError("Duplicate selected metadata identifier; review before annotation")
            enriched[identifier] = compact
        title = row.get("title") or ""
        categories = row.get("categories") or []
        hint = (isinstance(title, str) and bool(re.search(r"\b(laptop|notebook|chromebook|convertible|2.in.1|CF.19)\b", title, re.I))) or (
            isinstance(categories, list) and any(c in acquisition["filter"]["laptop_categories"] for c in categories))
        if identifier not in product_ids and hint and (not decision.include or re.search(r"\b(convertible|2.in.1|detachable)\b", title, re.I)):
            boundary.add({**compact, "prediction": decision.include, "pipeline_reason": decision.reason})
        if source_line % 10000 == 0:
            check_memory(limits["max_process_working_set_bytes"])
    if not stats.eof_observed or stats.invalid_records or stats.rows != report["metadata_scan"]["rows"]:
        raise ValueError("Incomplete/invalid metadata extraction")
    if not set(product_ids).issubset(enriched):
        raise ValueError("Selected KEEP products missing original metadata")
    output.mkdir(parents=True)
    records, private = [], []
    def add(item: dict, task: str, stratum: str, prediction: bool, reason: str, frame_n: int, sample_n: int):
        key = item.get("review_id", item["product_id"])
        annotation_id = stable_key({"task": task, "key": key}, seed + 6)[:24]
        columns = PRODUCT_COLUMNS if task == "product" else REVIEW_COLUMNS
        item["annotation_id"] = annotation_id
        item["product_url"] = f"https://www.amazon.com/dp/{item['product_id']}"
        item.update({column: "" for column in HUMAN_COLUMNS})
        human = _strings(item, columns)
        records.append((task, human))
        private.append({"annotation_id": annotation_id, "task": task, "stratum": stratum,
                        "prediction": prediction, "pipeline_reason": reason, "frame_population": frame_n,
                        "sample_size": sample_n, "inclusion_probability": sample_n / frame_n if frame_n and stratum != "diagnostic" else None,
                        "fixed_fingerprint": fixed_fingerprint(human),
                        "diagnostic_selection": "short (<5 normalized whitespace words) OR convertible/tablet product title" if task == "review" and stratum == "diagnostic" else "metadata laptop/category/convertible hint" if stratum == "diagnostic" else None})
    for identifier in product_ids:
        add(dict(enriched[identifier]), "product", "random_keep", True, "laptop_category_and_title", len(products), len(product_ids))
    for row in boundary.rows:
        item = {k: v for k, v in row.items() if k not in {"prediction", "pipeline_reason"}}
        add(item, "product", "diagnostic", row["prediction"], row["pipeline_reason"], boundary.count, len(boundary.rows))
    for stratum, rows, frame_n, prediction in review_groups:
        for row in rows:
            product = enriched.get(row["parent_asin"])
            if product is None:
                product = {"product_id": row["parent_asin"], **metadata_fields(None, {"metadata_status": "no_matching_parent_in_complete_source", "metadata_sha256": inputs["metadata"]["sha256"]})}
            item = {**product, "review_id": row["review_id"], "review_title": row["review_title"], "review_text": row["text"]}
            item["source_evidence"] = {**item["source_evidence"], "review_file": paths["reviews"].as_posix(),
                                       "review_sha256": inputs["reviews"]["sha256"], "review_line": row["source_line"]}
            add(item, "review", stratum, prediction, classify_product({"parent_asin": item["product_id"], "title": item["title"], "categories": item["categories"]}, acquisition["filter"]).reason if product.get("title") is not None else "not_in_selected_metadata_index", frame_n, len(rows))
    for task, columns in (("product", PRODUCT_COLUMNS), ("review", REVIEW_COLUMNS)):
        rows = [row for kind, row in records if kind == task]
        rows.sort(key=lambda row: stable_key({"annotation_id": row["annotation_id"]}, seed + 7))
        write_csv(output / f"{task}_annotation.csv", columns, rows)
    (output / "private_predictions.json").write_text(json.dumps(private, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result = {"version": VERSION, "status": "AWAITING_INDEPENDENT_HUMAN_ANNOTATION", "seed": seed,
              "created_utc": datetime.now(timezone.utc).isoformat(), "run_report": report_path.as_posix(),
              "run_report_sha256": sha256_file(report_path), "source_inputs": inputs,
              "rules": acquisition["filter"], "schema_aliases": acquisition["schema"],
              "rules_sha256": stable_key(acquisition["filter"], 0),
              "populations": {"products_keep": len(products), "products_boundary": boundary.count,
                              "reviews_valid_keep": n_keep, "reviews_metadata_reject": review_groups[1][2],
                              "reviews_diagnostic_remaining_keep": diagnostics.count,
                              "excluded_selected_but_invalid_reviews": report["groups"]["laptop"]["matched_reviews"] - n_keep},
              "samples": dict(Counter(f"{r['task']}:{r['stratum']}" for r in private)),
              "sampling": "Seeded SRS without replacement: products sorted unique IDs; KEEP physical valid-output indices; REJECT random ordered raw-line candidates conditioned on parent not in selected index. Diagnostic reservoir from explicit eligible frames, excluded from representative estimates. Annotation order independently shuffled; decisions/strata only in private sidecar.",
              "scope": "Product random frame: saved KEEP products. Review inference frame: valid saved KEEP plus all metadata-unselected REJECT source records. Excludes selected-but-invalid records; does not estimate recall of whole raw-source final-validity pipeline. Diagnostic review frame is KEEP-only; not a false-negative search.",
              "metadata_scan": asdict(stats), "raw_review_lines_read": line,
              "resources": {"elapsed_seconds": time.monotonic() - started, "decoded_read_bytes": decoded_bytes + stats.decoded_bytes, **process_memory()},
              "files": {p.name: {"sha256": sha256_file(p), "bytes": p.stat().st_size} for p in output.iterdir()}}
    (output / "manifest.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def _metrics(counts: dict) -> dict:
    tp, fp, fn, tn = (counts.get(k, 0) for k in ("TP", "FP", "FN", "TN"))
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    return {"confusion_matrix": {k: counts.get(k, 0) for k in ("TP", "FP", "FN", "TN")},
            "precision": precision, "recall": recall,
            "f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None}


def evaluate_independent_qa(kit: Path, annotations: dict[str, Path], *, annotator: str,
                            independent_human: bool = False,
                            ai_assisted_review: bool = False) -> dict:
    """Xác thực binding/evidence; chỉ ước tính số liệu có trọng số với các tầng hoàn chỉnh."""
    if not independent_human or not annotator.strip():
        raise ValueError("Explicit independent human declaration and annotator required")
    manifest = json.loads((kit / "manifest.json").read_text(encoding="utf-8"))
    private_path = kit / "private_predictions.json"
    if sha256_file(private_path) != manifest["files"][private_path.name]["sha256"]:
        raise ValueError("Prediction sidecar changed")
    predictions = json.loads(private_path.read_text(encoding="utf-8"))
    reference = {r["annotation_id"]: r for r in predictions}
    if len(reference) != len(predictions) or set(annotations) != {"product", "review"}:
        raise ValueError("Invalid kit/tasks")
    groups, comparisons, labels_by_product = defaultdict(Counter), [], defaultdict(set)
    for task, path in annotations.items():
        columns, rows = read_csv(path)
        if set(columns) != set(PRODUCT_COLUMNS if task == "product" else REVIEW_COLUMNS):
            raise ValueError("Annotation columns changed")
        ids = [r["annotation_id"] for r in rows]
        if len(set(ids)) != len(ids) or set(ids) != {k for k, v in reference.items() if v["task"] == task}:
            raise ValueError("Missing/extra/duplicate annotation IDs")
        for row in rows:
            ref = reference[row["annotation_id"]]
            if fixed_fingerprint(row) != ref["fixed_fingerprint"]:
                raise ValueError("Immutable evidence/source columns changed")
            label = row["human_label"].strip().lower()
            if label not in LABELS or row["human_error_reason"].strip() not in ERROR_REASONS:
                raise ValueError("Invalid human label or error reason")
            if label and not row["human_evidence"].strip():
                raise ValueError("Every human label including uncertain needs human evidence/reason")
            truth = LABELS[label]
            key = (task, ref["stratum"])
            category = "blank" if not label else "uncertain" if truth is None else (
                "TP" if ref["prediction"] and truth else "FP" if ref["prediction"] else "FN" if truth else "TN")
            groups[key][category] += 1
            if truth is not None:
                labels_by_product[row["product_id"]].add(truth)
            comparisons.append({"annotation_id": row["annotation_id"], "task": task,
                                "product_id": row["product_id"], "stratum": ref["stratum"],
                                "pipeline_prediction": ref["prediction"], "pipeline_reason": ref["pipeline_reason"],
                                "human_label": label, "outcome": category,
                                "human_error_reason": row["human_error_reason"] or ("unclassified" if category in {"FP", "FN"} else ""),
                                "human_evidence": row["human_evidence"], "human_notes": row["human_notes"]})
    conflicts = sorted(p for p, labels in labels_by_product.items() if len(labels) > 1)
    strata, weighted = {}, Counter()
    all_review_complete = True
    for (task, stratum), counts in groups.items():
        refs = [r for r in predictions if r["task"] == task and r["stratum"] == stratum]
        frame_n, sample_n = refs[0]["frame_population"], len(refs)
        if any(r["frame_population"] != frame_n or r["sample_size"] != sample_n for r in refs):
            raise ValueError("Inconsistent stratum sampling metadata")
        pending = counts["blank"] + counts["uncertain"]
        entry = {"sample_size": sample_n, "frame_population": frame_n, "counts": dict(counts),
                 "complete": pending == 0, "resolved_sample_confusion": _metrics(counts)["confusion_matrix"]}
        if stratum == "diagnostic":
            entry["metrics"] = None
            entry["note"] = "Diagnostic errors only; excluded from representative metrics."
        else:
            entry["precision"] = counts["TP"] / sample_n if task == "product" and not pending else None
            entry["recall"] = None
            entry["f1"] = None
            if stratum == "random_keep":
                entry["laptop_fraction_bounds"] = [counts["TP"] / sample_n, (counts["TP"] + pending) / sample_n]
            else:
                entry["laptop_fraction_bounds"] = [counts["FN"] / sample_n, (counts["FN"] + pending) / sample_n]
            if task == "review":
                all_review_complete &= pending == 0
                for key in ("TP", "FP", "FN", "TN"):
                    weighted[key] += counts[key] * frame_n / sample_n
        strata[f"{task}:{stratum}"] = entry
    if {("review", "random_keep"), ("review", "random_reject")} - groups.keys():
        all_review_complete = False
    weighted_metrics = _metrics(weighted) if all_review_complete and not conflicts else None
    if conflicts:
        for entry in strata.values():
            if "precision" in entry:
                entry["precision"] = None
    pending_total = sum(c["blank"] + c["uncertain"] for c in groups.values())
    return {"version": VERSION, "status": "ANNOTATION_COMPLETE_REVIEW_REQUIRED" if not pending_total and not conflicts else "PENDING_ANNOTATION_OR_ADJUDICATION",
            "annotator": annotator,
            "label_provenance": "human_verified_after_ai_assistance" if ai_assisted_review else "independent_human_declared",
            "annotation_process": "Human confirmed review and approval after AI suggestions; not fully blind annotation. Independence gate requires separate review." if ai_assisted_review else "Independent human verification self-declared; not proven by code.",
            "evaluated_utc": datetime.now(timezone.utc).isoformat(),
            "annotation_sha256": {task: sha256_file(path) for task, path in annotations.items()},
            "strata": strata, "review_weighted_estimates": weighted_metrics,
            "weighting": "Within representative review stratum h use N_h/n_h for each resolved record. Withhold population precision/recall/F1 until all random strata are resolved and no conflicting product labels. Diagnostic rows never enter estimates. Estimates are design-weighted point estimates, not exact population counts or confidence intervals.",
            "population_scope": manifest["scope"], "pending_or_uncertain": pending_total,
            "conflicting_product_labels": conflicts, "comparisons": comparisons,
            "error_reason_counts": dict(Counter(r["human_error_reason"] for r in comparisons if r["outcome"] in {"FP", "FN"})),
            "limitations": ["laptop-only findings", "Amazon rating-derived proxy-label noise (not evaluated here)",
                            "SemEval-to-Amazon platform/style shift within laptop reviews (not evaluated here)",
                            "small manually annotated gold set (this QA is not sentiment/ABSA gold)",
                            "Self-declared human provenance; script cannot prove independence. No plan gate automatically completed."]}


def write_evaluation(result: dict, output: Path) -> None:
    """Tạo bảng so sánh cụ thể và Markdown mà không thay đổi nhãn gán."""
    if output.exists():
        raise FileExistsError("Evaluation output already exists; use a new directory")
    output.mkdir(parents=True)
    (output / "evaluation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    rows = result["comparisons"]
    write_csv(output / "comparisons.csv", list(rows[0]), rows)
    errors = [r for r in rows if r["outcome"] in {"FP", "FN"}]
    write_csv(output / "errors.csv", list(rows[0]), errors)
    table = [{"stratum": key, "frame_population": val["frame_population"], "sample_size": val["sample_size"],
              **{k: val["counts"].get(k, 0) for k in ("TP", "FP", "FN", "TN", "blank", "uncertain")}}
             for key, val in result["strata"].items()]
    write_csv(output / "strata.csv", list(table[0]), table)
    text = ["# Independent Human QA evaluation", "", f"Status: {result['status']}",
            f"Annotator: {result['annotator']}; provenance: {result['label_provenance']}", "",
            result["annotation_process"], "",
            "| Stratum | N | n | TP | FP | FN | TN | Blank | Uncertain |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for row in table:
        text.append("| " + " | ".join(str(row[k]) for k in row) + " |")
    text += ["", "Review design-weighted metrics (null means not estimable yet):", "",
             "```json", json.dumps(result["review_weighted_estimates"], indent=2), "```", "",
             "Product random KEEP precision: " + str(result["strata"].get("product:random_keep", {}).get("precision")), "",
             "Conflicting product labels: " + str(result["conflicting_product_labels"]), "",
             result["weighting"], "", result["population_scope"], "",
             "FP = predicted KEEP / human non_laptop; FN = predicted REJECT / human laptop. Confusion rows are human truth, columns pipeline decision. Product KEEP-only sampling cannot estimate recall/F1. Blank and uncertain remain unresolved; bounds for stratum laptop fractions are in evaluation.json. Error causes come from human_error_reason; unfilled mismatch causes are unclassified, never AI-inferred.", "",
             "P1 acceptance requires review of evidence and adjudication; no checklists are changed automatically.", "",
             "Limitations: " + "; ".join(result["limitations"]) + "."]
    (output / "report.md").write_text("\n".join(text) + "\n", encoding="utf-8")
