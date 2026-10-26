"""siêu dữ liệu-đường dẫn acquisition/feasibility dựa trên tệp đầu tiên, được giới hạn trong bộ nhớ."""

import csv
import json
import re
import time
from collections import Counter
from contextlib import ExitStack
from dataclasses import asdict
from pathlib import Path

from src.data.acquisition import manifest_path, sha256_file
from src.data.laptop_filter import classify_product, parent_identifier
from src.data.loader import ScanStats, first_present, scan_jsonl
from src.data.survey import BottomSample, ReviewSurvey, estimated_size, normalize_for_survey
from src.data.validation import SchemaProfile, sample_reviews, stable_key


def source_info(path: Path) -> dict:
    """Xác minh nguồn bất biến đối với sidecar của nó khi có sẵn; ghi lại đầu vào cục bộ."""
    digest = sha256_file(path)
    sidecar = manifest_path(path)
    if sidecar.exists():
        manifest = json.loads(sidecar.read_text(encoding="utf-8"))
        if manifest["sha256"] != digest:
            raise ValueError(f"Source checksum mismatch: {path.name}")
        return {"name": path.name, "sha256": digest, "manifest": manifest,
                "complete_source": manifest.get("complete_source", False)}
    return {"name": path.name, "sha256": digest, "complete_source": False,
            "provenance": "local_input_source_completeness_unknown"}


def process_memory() -> dict:
    """Đọc quy trình hoạt động thực tế set/peak nơi nền tảng hiển thị nó."""
    import os
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        class Counters(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [
                (name, ctypes.c_size_t) for name in ("PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage", "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage", "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage")]
        counters = Counters()
        counters.cb = ctypes.sizeof(counters)
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.GetCurrentProcess.restype = wintypes.HANDLE
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
        if psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
            return {"working_set_bytes": counters.WorkingSetSize, "peak_working_set_bytes": counters.PeakWorkingSetSize}
    return {"working_set_bytes": "NOT_MEASURED", "peak_working_set_bytes": "NOT_MEASURED"}


def write_qa(path: Path, rows: list[dict]) -> None:
    """Tạo các cột quy tắc bất biến với con người nhãn trống, bảo tồn nhãn gán khi sử dụng lại."""
    columns = ["group", "source", "parent_asin", "title", "categories", "brand", "rule_include", "rule_reason", "stratum", "human_is_target_product", "human_notes"]
    if path.exists():
        with path.open(encoding="utf-8-sig", newline="") as handle:
            existing = list(csv.DictReader(handle))
        expected = [(r["parent_asin"], str(r["rule_include"]), r["rule_reason"]) for r in rows]
        if [(r["parent_asin"], r["rule_include"], r["rule_reason"]) for r in existing] != expected:
            raise ValueError("QA sample/rule changed; use a new run directory, preserve human labels")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({**row, "categories": json.dumps(row["categories"], ensure_ascii=False), "human_is_target_product": "", "human_notes": ""})


def qa_rule_hash(path: Path) -> str:
    """Các cột quy tắc vân tay trong khi chỉ cho phép con người chỉnh sửa các cột gán nhãn."""
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = [{key: value for key, value in row.items() if key not in {"human_is_target_product", "human_notes"}}
                for row in csv.DictReader(handle)]
    return stable_key({"rows": rows}, 0)


def check_memory(max_bytes: int) -> None:
    """Thực thi kiểm tra giới hạn bộ làm việc thực tế trên các nền tảng được hỗ trợ."""
    usage = process_memory()["working_set_bytes"]
    if isinstance(usage, int) and usage > max_bytes:
        raise MemoryError("Process working-set budget exceeded; unfinished output is not a completed run")


def run_feasibility(metadata: Path, reviews: Path | None, output: Path, qa_dir: Path,
                    config: dict, acquisition: dict, *, source: str, mode: str = "probe",
                    seed: int = 42, allow_large_scan: bool = False, metadata_only: bool = False) -> dict:
    """Truyền chỉ mục siêu dữ liệu sau đó khớp với review; không có cơ sở dữ liệu hoặc danh sách có kích thước kho văn bản."""
    if mode not in {"probe", "scan"}:
        raise ValueError("mode must be probe or scan")
    if mode == "scan" and not allow_large_scan:
        raise ValueError("Large scan requires explicit authorization; use --allow-large-scan")
    if config["groups"] != ["laptop"]:
        raise ValueError("Only the laptop project domain is supported")
    if reviews is None and not metadata_only:
        raise ValueError("Reviews input required unless metadata_only")
    # Không bao giờ cho phép thư mục một lần chạy chứa hoặc thay thế dữ liệu nguồn hay nhãn gán.
    from src.config import dataset_path
    for protected in (dataset_path("amazon_raw").parent, qa_dir, metadata, *([reviews] if reviews else [])):
        if output.resolve() == protected.resolve() or output.resolve() in protected.resolve().parents or protected.resolve() in output.resolve().parents:
            raise ValueError("Output must be separate from raw inputs and human annotations")
    limits, groups = config["limits"], config["groups"]
    read_limit, output_limit = limits[f"max_{mode}_read_bytes"], limits[f"max_{mode}_output_bytes"]
    checksum_bytes = metadata.stat().st_size + (reviews.stat().st_size if reviews and not metadata_only else 0)
    if checksum_bytes >= read_limit:
        raise ValueError("Input too large for selected mode, including checksum I/O; explicit budget change required")
    started = time.monotonic()
    inputs = {"metadata": source_info(metadata)}
    if not metadata_only:
        inputs["reviews"] = source_info(reviews)
    for kind, info in inputs.items():
        expected = config.get("sources", {}).get(source, {}).get(f"{kind}_url")
        if expected and info.get("manifest", {}).get("source_url") != expected:
            info["complete_source"] = False
            info["provenance"] = "source_url_mismatch_or_missing"
    settings_hash = stable_key({"config": config, "acquisition": acquisition, "seed": seed, "source": source, "mode": mode, "metadata_only": metadata_only}, seed)
    report_path = output / "report.json"
    if report_path.exists():
        previous = json.loads(report_path.read_text(encoding="utf-8"))
        if "qa_rule_sha256" not in previous:
            raise ValueError("Previous run lacks immutable QA fingerprints; choose a new run directory")
        if previous["inputs"] != inputs or previous["settings_sha256"] != settings_hash:
            raise ValueError("Existing run differs; choose a new output directory")
        for name, digest in previous["output_sha256"].items():
            if sha256_file(output / name) != digest:
                raise ValueError("Existing output checksum mismatch; do not overwrite")
        for name, digest in previous["qa_rule_sha256"].items():
            if not (qa_dir / name).exists() or qa_rule_hash(qa_dir / name) != digest:
                raise ValueError("Existing QA rule columns missing/changed; preserve human annotations")
        return previous
    if output.exists() and any(output.iterdir()):
        raise ValueError("Existing unfinished run must be inspected; use a new directory")
    output.mkdir(parents=True, exist_ok=True)
    deadline = started + limits[f"max_{mode}_seconds"]
    index, index_bytes = {}, 0
    metadata_stats, review_stats = ScanStats(), ScanStats()
    review_stats.stop_reason = "not_started"
    def fail(stage: str, message: str) -> None:
        diagnostic = {"status": "BLOCKED", "stage": stage, "reason": message,
                      "NEXT_ACTION": "Inspect source/provenance and resource budget; use a new run directory",
                      "source_coverage_complete": False, "inputs": inputs,
                      "metadata_scan": asdict(metadata_stats), "review_scan": asdict(review_stats),
                      "resources": {"estimated_index_bytes": index_bytes, **process_memory()}}
        (output / "failure.json").write_text(json.dumps(diagnostic, indent=2) + "\n", encoding="utf-8")

    def guarded_scan(path: Path, stats: ScanStats, stage: str, **kwargs):
        try:
            check_memory(limits["max_process_working_set_bytes"])
            for line, row in scan_jsonl(path, stats, **kwargs):
                if line == 1 or line % 1000 == 0:
                    check_memory(limits["max_process_working_set_bytes"])
                yield line, row
        except MemoryError:
            stats.stop_reason = "memory_limit"
            fail(stage, "Process working-set resource budget exceeded")
            raise
        except ValueError as exc:
            fail(stage, str(exc))
            raise
    profiles = {"metadata": SchemaProfile(), "reviews": SchemaProfile()}
    decisions = {group: Counter() for group in groups}
    baseline = Counter()
    counts = Counter()
    qa = {group: {kind: BottomSample(size, seed) for kind, size in config["qa"].items()} for group in groups}
    schema = acquisition["schema"]
    products_path = output / "products.jsonl"
    total_written = 0
    with products_path.open("x", encoding="utf-8", newline="\n") as products_out:
        for line, row in guarded_scan(metadata, metadata_stats, "metadata", max_rows=limits[f"{mode}_metadata_records"], max_bytes=read_limit - checksum_bytes,
                                    deadline=deadline, max_record_bytes=limits["max_record_bytes"]):
            profiles["metadata"].add(row)
            try:
                identifier = parent_identifier(row, schema["metadata_id"])
            except ValueError:
                counts["invalid_metadata_identifier"] += 1
                continue
            baseline_decision = classify_product(row, acquisition["filter"])
            classifications = {"laptop": baseline_decision}
            baseline[baseline_decision.reason] += 1
            details = row.get("details", {})
            if isinstance(details, str):
                try:
                    details = json.loads(details)
                except ValueError:
                    details = {}
            brand = details.get("Brand") if isinstance(details, dict) else None
            if not isinstance(brand, str) or not brand.strip():
                brand = None
            compact = {"parent_asin": identifier, "title": row.get("title"), "categories": row.get("categories"), "brand": brand}
            chosen = [group for group, decision in classifications.items() if decision.include]
            if identifier in index and (not chosen or index[identifier] != {**compact, "group": chosen[0]}):
                raise ValueError("Conflicting selected product metadata; stop before review join")
            if chosen:
                item = {**compact, "group": chosen[0]}
                if identifier in index:
                    if index[identifier] != item:
                        raise ValueError("Conflicting selected product metadata; stop before review join")
                    counts["duplicate_selected_metadata"] += 1
                    continue
                else:
                    size = estimated_size(item) + estimated_size(identifier) + 128
                    if len(index) >= limits["max_index_products"] or index_bytes + size > limits["max_index_estimated_bytes"]:
                        metadata_stats.stop_reason = "memory_limit"
                        break
                    encoded = json.dumps(item, ensure_ascii=False) + "\n"
                    if total_written + len(encoded.encode("utf-8")) > output_limit:
                        metadata_stats.stop_reason = "output_limit"
                        break
                    index[identifier] = item
                    index_bytes += size
                    products_out.write(encoded)
                    total_written += len(encoded.encode("utf-8"))
            for group, decision in classifications.items():
                decisions[group][decision.reason] += 1
                title = row.get("title") if isinstance(row.get("title"), str) else ""
                hint = bool(re.search(r"\b(laptop|notebook|chromebook)\b", title, re.I))
                allowed = acquisition["filter"]["laptop_categories"]
                category_hint = isinstance(row.get("categories"), list) and any(c in allowed for c in row["categories"])
                kind = "included" if decision.include else "excluded_near_boundary" if hint or category_hint or decision.reason == "ambiguous_multiple_groups" else "excluded_other"
                qa[group][kind].add({**compact, "group": group, "source": source, "rule_include": decision.include, "rule_reason": decision.reason, "stratum": kind})
    if metadata_stats.stop_reason in {"memory_limit", "output_limit"}:
        review_stats.stop_reason = "not_started"
        fail("metadata", "Metadata index exceeded resource budget; no reviews joined")
        raise ValueError("Metadata index exceeded resource budget; no reviews joined. Inspect budgets before a new run.")
    metadata_complete = metadata_stats.eof_observed and inputs["metadata"]["complete_source"]
    if mode == "scan" and (not metadata_complete or metadata_stats.invalid_records or counts["invalid_metadata_identifier"]):
        review_stats.stop_reason = "not_started"
        fail("metadata", "Full-pool scan requires complete, valid metadata with matching source provenance; no reviews joined")
        raise ValueError("Full-pool scan requires complete metadata; see failure.json")
    for group in groups:
        write_qa(qa_dir / f"{source}_{group}_{settings_hash[:12]}.csv", [row for sample in qa[group].values() for row in sample.rows()])
    if metadata_only:
        review_stats.stop_reason = "not_started"
        result = {"status": "DONE" if metadata_complete else "PENDING", "mode": mode,
                  "metadata_only": True, "source": source, "inputs": inputs,
                  "settings_sha256": settings_hash, "source_coverage_complete": False,
                  "metadata_coverage_complete": metadata_complete,
                  "metadata_scan": asdict(metadata_stats), "review_scan": asdict(review_stats),
                  "candidate_products": {g: sum(p["group"] == g for p in index.values()) for g in groups},
                  "filter_decisions": {g: dict(decisions[g]) for g in groups},
                  "baseline_laptop_filter_decisions": dict(baseline), "join_counts": dict(counts),
                  "resources": {"elapsed_seconds": time.monotonic() - started,
                                "estimated_index_bytes": index_bytes, "checksum_read_bytes": checksum_bytes,
                                "decoded_read_bytes": metadata_stats.decoded_bytes, **process_memory()},
                  "output_sha256": {products_path.name: sha256_file(products_path)},
                  "qa_rule_sha256": {f"{source}_{g}_{settings_hash[:12]}.csv": qa_rule_hash(qa_dir / f"{source}_{g}_{settings_hash[:12]}.csv") for g in groups}}
        report_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        return result
    survey = config["survey"]
    metrics = {group: ReviewSurvey(survey["aspect_keywords"][group], survey["short_review_words"], survey["min_absa_proxy_words"], limits["max_unique_text_hashes_per_group"]) for group in groups}
    samples = {group: BottomSample(limits["max_sample_rows_per_group"], seed, limits["max_sample_estimated_bytes_per_group"]) for group in groups}
    matched, invalid, missing = {g: 0 for g in groups}, {g: Counter() for g in groups}, {g: Counter() for g in groups}
    remaining_read = read_limit - checksum_bytes - metadata_stats.decoded_bytes
    if remaining_read <= 0:
        review_stats.stop_reason = "byte_limit"
    else:
        review_stats.stop_reason = "source_eof"
    with ExitStack() as stack:
        handles = {g: stack.enter_context((output / f"{g}_valid.jsonl").open("x", encoding="utf-8", newline="\n")) for g in groups}
        stream = guarded_scan(reviews, review_stats, "reviews", max_rows=limits[f"{mode}_review_records"], max_bytes=remaining_read,
                            deadline=deadline, max_record_bytes=limits["max_record_bytes"]) if remaining_read > 0 else iter(())
        for line, row in stream:
            profiles["reviews"].add(row)
            try:
                identifier = parent_identifier(row, schema["review_parent_id"])
            except ValueError:
                counts["invalid_review_identifier"] += 1
                continue
            product = index.get(identifier)
            if product is None:
                counts["not_in_selected_metadata_index"] += 1
                continue
            group = product["group"]
            matched[group] += 1
            for field, aliases in (("text", schema["review_text"]), ("rating", schema["review_rating"]),
                                   ("timestamp", schema["review_timestamp"]), ("helpful_vote", schema["review_helpful"]),
                                   ("verified_purchase", ["verified_purchase"]), ("user_id", ["user_id"]),
                                   ("review_title", schema.get("review_title", ["title"])), ("asin", ["asin"])):
                if not any(key in row and row[key] is not None for key in aliases):
                    missing[group][field] += 1
            try:
                text = first_present(row, schema["review_text"])
                rating = first_present(row, schema["review_rating"])
                if not isinstance(text, str) or not normalize_for_survey(text):
                    invalid[group]["empty_or_invalid_text"] += 1
                    continue
                if isinstance(rating, bool) or not isinstance(rating, (int, float)) or rating not in (1, 2, 3, 4, 5):
                    invalid[group]["invalid_rating"] += 1
                    continue
                candidate = {"review_id": f"amazon2023:{inputs['reviews']['sha256']}:{line}", "source": source, "source_line": line, "group": group,
                             "parent_asin": identifier, "asin": row.get("asin"), "user_id": row.get("user_id"),
                             "review_title": first_present(row, schema.get("review_title", ["title"])),
                             "text": text, "rating": int(rating), "product_title": product["title"], "brand": product["brand"],
                             "timestamp": first_present(row, schema["review_timestamp"]), "helpful_vote": first_present(row, schema["review_helpful"]), "verified_purchase": row.get("verified_purchase")}
            except ValueError:
                invalid[group]["conflicting_aliases"] += 1
                continue
            encoded = json.dumps(candidate, ensure_ascii=False) + "\n"
            if total_written + len(encoded.encode("utf-8")) > output_limit:
                invalid[group]["output_budget_not_saved"] += 1
                review_stats.stop_reason = "output_limit"
                break
            handles[group].write(encoded)
            total_written += len(encoded.encode("utf-8"))
            metrics[group].add(candidate)
            samples[group].add(candidate)
    if review_stats.rows != review_stats.invalid_records + counts["invalid_review_identifier"] + counts["not_in_selected_metadata_index"] + sum(matched.values()):
        raise ValueError("Review row conservation failed")
    group_results = {}
    sample_stop_reason = "completed"
    for group in groups:
        if matched[group] != metrics[group].count + sum(invalid[group].values()):
            raise ValueError("Matched/valid/invalid row conservation failed")
        reservoir = samples[group].rows()
        # Bể chứa băm đáy toàn cầu vẫn bị giới hạn; giới hạn sản phẩm được áp dụng cho điều đó
        # hồ chứa, chưa bao giờ tuyên bố đáp ứng hạn ngạch theo tỷ lệ toàn bộ hồ chứa.
        diversified, product_counts = [], Counter()
        for row in sample_reviews(reservoir, len(reservoir), seed):
            if product_counts[row["parent_asin"]] < limits["max_reviews_per_product_in_sample"]:
                diversified.append(row)
                product_counts[row["parent_asin"]] += 1
        sample_path = output / f"{group}_sample.jsonl"
        saved = []
        with sample_path.open("x", encoding="utf-8", newline="\n") as handle:
            for row in diversified:
                encoded = json.dumps(row, ensure_ascii=False) + "\n"
                byte_count = len(encoded.encode("utf-8"))
                if total_written + byte_count > output_limit:
                    sample_stop_reason = "output_limit"
                    break
                handle.write(encoded)
                total_written += byte_count
                saved.append(row)
        diversified = saved
        product_counts = Counter(row["parent_asin"] for row in saved)
        group_results[group] = {"candidate_products": sum(p['group'] == group for p in index.values()), "matched_reviews": matched[group],
                               **metrics[group].result(), "invalid_reviews": dict(invalid[group]), "missing_fields_on_matched": dict(missing[group]),
                               "filter_decisions": dict(decisions[group]), "filter_validation": "unvalidated",
                               "sample_reviews": len(diversified), "sample_rating_distribution": dict(Counter(str(r['rating']) for r in diversified)),
                               "sample_unique_products": len(product_counts), "sample_max_reviews_per_product": max(product_counts.values(), default=0),
                               "sample_budget_rejections": samples[group].budget_rejections, "sample_estimated_bytes": samples[group].bytes}
    complete = metadata_stats.eof_observed and review_stats.eof_observed and all(i["complete_source"] for i in inputs.values())
    report = {"version": config["version"], "purpose": config["purpose"], "source": source, "mode": mode, "inputs": inputs,
              "settings_sha256": settings_hash, "seed": seed, "source_coverage_complete": complete,
              "dataset_status": "candidate_pool_requires_human_QA_and_language_validation" if complete and mode == "scan" else "exploratory_subset_not_final_dataset",
              "metadata_scan": asdict(metadata_stats), "review_scan": asdict(review_stats), "join_counts": dict(counts),
              "metadata_coverage_complete": metadata_complete, "sample_stop_reason": sample_stop_reason,
              "baseline_laptop_filter_decisions": dict(baseline),
              "record_policy": "oversized lines skipped with bounded drainage; JSON errors counted; corrupt gzip fails",
              "join_definition": "target match against selected metadata; not_in_selected_index conflates out-of-scope and absent metadata",
              "groups": group_results, "metadata_schema": profiles['metadata'].to_dict(), "review_schema": profiles['reviews'].to_dict(),
              "resources": {"elapsed_seconds": time.monotonic() - started, "estimated_index_bytes": index_bytes,
                            "index_products": len(index), "bytes_written_jsonl": total_written,
                            "io_passes": {"checksum": 1, "metadata": 1, "reviews": 1},
                            "checksum_read_bytes": checksum_bytes,
                            "decoded_read_bytes": metadata_stats.decoded_bytes + review_stats.decoded_bytes, **process_memory()},
              "limitations": ["prefixes are not representative", "language NOT_MEASURED", "keyword aspect coverage is heuristic", "filters unvalidated", "project remains laptop-only"]}
    report["output_sha256"] = {path.name: sha256_file(path) for path in output.glob("*.jsonl")}
    report["qa_rule_sha256"] = {f"{source}_{group}_{settings_hash[:12]}.csv": qa_rule_hash(qa_dir / f"{source}_{group}_{settings_hash[:12]}.csv") for group in groups}
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report
