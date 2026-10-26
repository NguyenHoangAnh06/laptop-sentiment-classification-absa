"""Chỉ kiểm tra vật cố tổng hợp; không có bằng chứng đánh giá so sánh hoặc con người gán nhãn."""

import copy
import csv
import gzip
import io
import json
import time
import urllib.request

import pytest

from src.config import load_config
from src.data.acquisition import acquire
from src.data.acquisition import sha256_file
from src.data.feasibility import check_memory, run_feasibility
from src.data.filter_qa import validate_product_qa
from src.data.loader import ScanStats, scan_jsonl
from src.data.laptop_filter import classify_product
from src.data.survey import BottomSample, ReviewSurvey, normalize_for_survey


def product(identifier, title, categories):
    return {"parent_asin": identifier, "title": title, "categories": categories, "details": {"Brand": "Fixture Brand"}}


@pytest.mark.parametrize("source,seconds,byte_limit,filename", [
    ("metadata", 3600, 1400000000, "meta_Electronics.jsonl.gz"),
    ("reviews", 10800, 6600000000, "Electronics.jsonl.gz"),
])
def test_full_acquisition_cli_uses_source_specific_time_budget(tmp_path, monkeypatch, capsys,
                                                            source, seconds, byte_limit, filename):
    from scripts import acquire_p1
    calls = []
    monkeypatch.setattr("sys.argv", ["acquire_p1", "--source", source, "--full", "--allow-large-download"])
    monkeypatch.setattr(acquire_p1, "dataset_path", lambda key: tmp_path)

    def fake_acquire(url, destination, **kwargs):
        calls.append((url, destination, kwargs))
        return {"fixture": True}

    monkeypatch.setattr(acquire_p1, "acquire", fake_acquire)
    acquire_p1.main()
    assert calls == [(load_config("feasibility")["sources"]["Electronics"][f"{source}_url"],
                      tmp_path / filename, {"max_bytes": byte_limit, "max_seconds": seconds})]
    assert json.loads(capsys.readouterr().out) == {"fixture": True}
    assert not list(tmp_path.iterdir())  # Không có mạng hoặc ghi thô trong lịch thi đấu CLI.


@pytest.mark.parametrize("title,categories,expected", [
    ("Fixture Laptop", ["Computers & Accessories", "Laptops"], True),
    ("Fixture 2-in-1 Convertible Laptop Tablet Mode", ["Computers & Tablets", "Laptops", "Traditional Laptops"], True),
    ("Fixture Chromebook", ["Notebook Computers"], True),
    ("Apple iPad Tablet", ["Computer Tablets"], False),
    ("Laptop Charger", ["Laptops"], False),
    ("Laptop Desktop", ["Desktop Computers"], False),
    ("Laptop Sleeve", ["Laptop Accessories"], False),
    ("Model-only CF19 Tablet PC", ["Laptops"], False),
    ("Fixture Laptop", [], False),
])
def test_laptop_filter_including_convertibles(title, categories, expected):
    assert classify_product(product("fixture", title, categories), load_config("acquisition")["filter"]).include is expected


def inputs(tmp_path):
    meta, reviews = tmp_path / "metadata.jsonl", tmp_path / "reviews.jsonl"
    products = [product("l", "Fixture Laptop", ["Laptops"]), product("s", "Fixture smartphone", ["Cell Phones"]), product("t", "Fixture tablet", ["Tablets"]), product("a", "Laptop Charger", ["Laptops"])]
    meta.write_text("\n".join(json.dumps(row) for row in products) + "\n", encoding="utf-8")
    rows = [
        {"parent_asin": "l", "text": "Battery is not good &amp; screen is bad.", "rating": 1},
        {"parent_asin": "l", "text": "Battery is not good &amp; screen is bad.", "rating": 1},
        {"parent_asin": "s", "text": "Good camera", "rating": 5},
        {"parent_asin": "t", "text": "<p> </p>", "rating": 3},
        {"parent_asin": "t", "text": "Nice screen", "rating": 6},
        {"parent_asin": "a", "text": "not a target", "rating": 5},
        {"parent_asin": "unseen", "text": "unknown", "rating": 3},
        {"asin": "l", "text": "do not fallback", "rating": 5},
        {"parent_asin": "s", "text": "different", "reviewText": "conflicting", "rating": 5},
    ]
    reviews.write_text("\n".join(json.dumps(row) for row in rows) + "\n{broken}\n", encoding="utf-8")
    return meta, reviews


def run(tmp_path, meta, reviews, config=None, **kwargs):
    return run_feasibility(meta, reviews, tmp_path / "result", tmp_path / "qa", config or load_config("feasibility"), load_config("acquisition"), source="Fixture", **kwargs)


def test_metadata_first_join_quality_counts_checksum_and_qa(tmp_path):
    meta, reviews = inputs(tmp_path)
    result = run(tmp_path, meta, reviews)
    assert result["groups"]["laptop"]["valid_reviews"] == 2
    assert result["groups"]["laptop"]["duplicate_percentage"] == 50
    assert set(result["groups"]) == {"laptop"}
    assert result["review_scan"]["invalid_records"] == 1
    assert result["join_counts"]["not_in_selected_metadata_index"] == 6
    assert result["join_counts"]["invalid_review_identifier"] == 1
    assert result["groups"]["laptop"]["language_distribution"] == "NOT_MEASURED"
    assert result["dataset_status"] == "exploratory_subset_not_final_dataset"
    assert result["source_coverage_complete"] is False
    qa = next((tmp_path / "qa").glob("*laptop*.csv"))
    assert validate_product_qa(qa, 1)["status"] == "unvalidated"
    with qa.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields, qa_rows = reader.fieldnames, list(reader)
    qa_rows[0]["human_notes"] = "Fixture human note to preserve on rerun"
    with qa.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(qa_rows)
    assert run(tmp_path, meta, reviews) == result
    assert "Fixture human note" in qa.read_text(encoding="utf-8-sig")
    output = tmp_path / "result" / "laptop_valid.jsonl"
    output.write_text("tampered", encoding="utf-8")
    with pytest.raises(ValueError, match="checksum"):
        run(tmp_path, meta, reviews)


def test_scan_gate_precedes_source_access(tmp_path):
    with pytest.raises(ValueError, match="authorization"):
        run(tmp_path, tmp_path / "not-created", tmp_path / "not-created", mode="scan")


def test_probe_rejects_large_checksum_io(tmp_path):
    meta, reviews = inputs(tmp_path)
    config = copy.deepcopy(load_config("feasibility"))
    config["limits"]["max_probe_read_bytes"] = 1
    with pytest.raises(ValueError, match="too large"):
        run(tmp_path, meta, reviews, config)


def test_process_memory_guard(monkeypatch):
    monkeypatch.setattr("src.data.feasibility.process_memory", lambda: {"working_set_bytes": 1024})
    with pytest.raises(MemoryError, match="working-set"):
        check_memory(1000)


def test_memory_bound_stops_before_review_join(tmp_path):
    meta, reviews = inputs(tmp_path)
    with meta.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(product("l2", "Second Fixture Laptop", ["Laptops"])) + "\n")
    config = copy.deepcopy(load_config("feasibility"))
    config["limits"]["max_index_products"] = 1
    with pytest.raises(ValueError, match="resource budget"):
        run(tmp_path, meta, reviews, config)
    assert not (tmp_path / "result" / "laptop_valid.jsonl").exists()


def test_stream_reader_limits_invalid_json_and_corrupt_gzip(tmp_path):
    path = tmp_path / "fixture.jsonl"
    path.write_text('{"ok":1}\n[]\n{"ok":2}\n', encoding="utf-8")
    stats = ScanStats()
    rows = list(scan_jsonl(path, stats, max_rows=2, max_bytes=1000, deadline=time.monotonic() + 5))
    assert rows == [(1, {"ok": 1})]
    assert stats.rows == 2 and stats.invalid_records == 1 and stats.stop_reason == "record_limit"
    broken = tmp_path / "bad.gz"
    broken.write_bytes(b"not gzip")
    with pytest.raises(ValueError, match="corrupt"):
        list(scan_jsonl(broken, ScanStats(), max_rows=5, max_bytes=1000, deadline=time.monotonic() + 5))
    bounded = ScanStats()
    assert list(scan_jsonl(path, bounded, max_rows=100, max_bytes=2, deadline=time.monotonic() + 5)) == []
    assert bounded.decoded_bytes == 2 and bounded.stop_reason == "byte_limit"


def test_sampler_reproducibility_and_bounds():
    rows = [{"id": i} for i in range(100)]
    a, b = BottomSample(5, 42), BottomSample(5, 42)
    for row in rows:
        a.add(row)
    for row in reversed(rows):
        b.add(row)
    assert a.rows() == b.rows()
    assert len(a.rows()) == 5
    limited = BottomSample(10, 42, max_bytes=1)
    limited.add({"id": 1})
    assert limited.rows() == [] and limited.budget_rejections == 1


def test_negation_normalization_and_duplicate_cap():
    assert normalize_for_survey("<p>Not good! Never again.</p> &amp; bad") == "Not good! Never again. & bad"
    survey = ReviewSurvey(["battery"], 5, 10, 1)
    for text in ("not good", "not bad"):
        survey.add({"parent_asin": "fixture", "text": text, "rating": 3, "brand": None})
    assert survey.result()["duplicate_percentage"] == "NOT_MEASURED"


def test_network_loss_keeps_partial_unfinalized_and_no_resume(tmp_path, monkeypatch):
    class Response(io.BytesIO):
        headers = {"Content-Length": "100"}
        url = "https://fixture.invalid/source"

    monkeypatch.setattr(urllib.request, "urlopen", lambda *args, **kwargs: Response(b"too short"))
    path = tmp_path / "raw.jsonl"
    with pytest.raises(ValueError, match="Incomplete HTTP"):
        acquire("https://fixture.invalid/source", path, max_bytes=1000)
    assert not path.exists()
    assert path.with_suffix(".jsonl.partial").exists()
    failure = json.loads(path.with_suffix(".jsonl.partial.failure.json").read_text())
    assert failure["finalized"] is False and failure["resume_supported"] is False
    with pytest.raises(ValueError, match="partial"):
        acquire("https://fixture.invalid/source", path)


def test_corrupt_network_gzip_does_not_create_raw(tmp_path, monkeypatch):
    class Response(io.BytesIO):
        headers = {}
        url = "https://fixture.invalid/source.gz"

    monkeypatch.setattr(urllib.request, "urlopen", lambda *args, **kwargs: Response(b"bad gzip"))
    path = tmp_path / "raw.jsonl"
    with pytest.raises(OSError):
        acquire("https://fixture.invalid/source.gz", path, limit=2)
    assert not path.exists()


def test_complete_fixture_scan_separates_source_coverage_and_human_validation(tmp_path):
    meta, reviews = inputs(tmp_path)
    for path in (meta, reviews):
        path.with_suffix(path.suffix + ".manifest.json").write_text(json.dumps({"sha256": sha256_file(path), "complete_source": True, "source_url": "https://fixture.invalid"}), encoding="utf-8")
    result = run(tmp_path, meta, reviews, mode="scan", allow_large_scan=True)
    assert result["source_coverage_complete"] is True
    assert result["dataset_status"] == "candidate_pool_requires_human_QA_and_language_validation"
    assert result["groups"]["laptop"]["filter_validation"] == "unvalidated"


def test_sample_product_cap_and_output_budget(tmp_path):
    meta, reviews = inputs(tmp_path)
    config = copy.deepcopy(load_config("feasibility"))
    config["limits"]["max_reviews_per_product_in_sample"] = 1
    config["limits"]["max_probe_output_bytes"] = 2000
    result = run(tmp_path, meta, reviews, config)
    assert result["groups"]["laptop"]["sample_max_reviews_per_product"] <= 1
    assert result["resources"]["bytes_written_jsonl"] <= 2000
    assert sum(path.stat().st_size for path in (tmp_path / "result").glob("*.jsonl")) <= 2000


def complete_manifests(meta, reviews):
    for path in (meta, reviews):
        path.with_suffix(path.suffix + ".manifest.json").write_text(json.dumps(
            {"sha256": sha256_file(path), "complete_source": True, "source_url": "https://fixture.invalid"}), encoding="utf-8")


@pytest.mark.parametrize("cause", ["record_limit", "byte_limit", "time_limit", "provenance"])
def test_full_scan_blocks_incomplete_metadata_and_records_diagnostic(tmp_path, cause):
    meta, reviews = inputs(tmp_path)
    complete_manifests(meta, reviews)
    config = copy.deepcopy(load_config("feasibility"))
    if cause == "record_limit":
        config["limits"]["scan_metadata_records"] = 1
    elif cause == "byte_limit":
        config["limits"]["max_scan_read_bytes"] = meta.stat().st_size + reviews.stat().st_size + 2
    elif cause == "time_limit":
        config["limits"]["max_scan_seconds"] = -1
    else:
        meta.with_suffix(".jsonl.manifest.json").unlink()
    with pytest.raises(ValueError, match="complete metadata"):
        run(tmp_path, meta, reviews, config, mode="scan", allow_large_scan=True)
    diagnostic = json.loads((tmp_path / "result/failure.json").read_text())
    assert diagnostic["source_coverage_complete"] is False
    assert diagnostic["review_scan"]["rows"] == 0
    assert diagnostic["review_scan"]["stop_reason"] == "not_started"
    assert not (tmp_path / "result/laptop_valid.jsonl").exists()
    assert diagnostic["metadata_scan"]["stop_reason"] == (cause if cause != "provenance" else "source_eof")


def test_probe_can_use_metadata_subset(tmp_path):
    meta, reviews = inputs(tmp_path)
    config = copy.deepcopy(load_config("feasibility"))
    config["limits"]["probe_metadata_records"] = 1
    result = run(tmp_path, meta, reviews, config)
    assert result["metadata_scan"]["stop_reason"] == "record_limit"
    assert not result["metadata_coverage_complete"]
    assert result["groups"]["laptop"]["valid_reviews"] == 2


def test_partial_review_scan_is_never_full_coverage(tmp_path):
    meta, reviews = inputs(tmp_path)
    complete_manifests(meta, reviews)
    config = copy.deepcopy(load_config("feasibility"))
    config["limits"]["scan_review_records"] = 1
    result = run(tmp_path, meta, reviews, config, mode="scan", allow_large_scan=True)
    assert result["metadata_coverage_complete"]
    assert result["review_scan"]["stop_reason"] == "record_limit"
    assert not result["source_coverage_complete"]


@pytest.mark.parametrize("compressed", [False, True])
def test_oversized_line_drains_once_without_parsing_tail(tmp_path, compressed):
    data = b'{"huge":"' + b"x" * 150000 + b'"}\n{"ok":2}\n'
    path = tmp_path / ("fixture.gz" if compressed else "fixture.jsonl")
    path.write_bytes(gzip.compress(data) if compressed else data)
    stats = ScanStats()
    assert list(scan_jsonl(path, stats, max_rows=10, max_bytes=200000,
                           deadline=time.monotonic() + 5, max_record_bytes=100)) == [(2, {"ok": 2})]
    assert stats.rows == 2 and stats.oversized_records == stats.invalid_records == 1
    assert stats.decoded_bytes == len(data) and stats.eof_observed


def test_oversized_drain_respects_byte_budget(tmp_path):
    path = tmp_path / "huge.jsonl"
    path.write_bytes(b"x" * 200000 + b'\n{"ok":2}\n')
    stats = ScanStats()
    assert list(scan_jsonl(path, stats, max_rows=10, max_bytes=1000,
                           deadline=time.monotonic() + 5, max_record_bytes=100)) == []
    assert stats.stop_reason == "byte_limit" and stats.decoded_bytes == 1000
    assert not stats.eof_observed and stats.oversized_records == 1


@pytest.mark.parametrize("data,malformed,truncated", [(b'{bad}\n', 1, 0), (b'{"bad":', 0, 1), (b'{"ok":1}', 0, 0)])
def test_malformed_and_suspected_truncated_record_separate(tmp_path, data, malformed, truncated):
    path = tmp_path / "fixture.jsonl"
    path.write_bytes(data)
    stats = ScanStats()
    list(scan_jsonl(path, stats, max_rows=10, max_bytes=1000, deadline=time.monotonic() + 5))
    assert stats.malformed_records == malformed and stats.truncated_records == truncated
    assert stats.eof_observed


def test_truncated_gzip_reports_corrupt_source(tmp_path):
    path = tmp_path / "fixture.gz"
    path.write_bytes(gzip.compress(b'{"ok":1}\n')[:-5])
    stats = ScanStats()
    with pytest.raises(ValueError, match="corrupt"):
        list(scan_jsonl(path, stats, max_rows=10, max_bytes=1000, deadline=time.monotonic() + 5))
    assert stats.stop_reason == "corrupt_source" and not stats.eof_observed


def test_review_optional_fields_preserved_or_null(tmp_path):
    meta, reviews = inputs(tmp_path)
    rows = [json.loads(line) for line in reviews.read_text().splitlines()[:-1]]
    fields = {"user_id": "fixture-user", "title": "Unchanged title", "asin": "variant", "timestamp": 123,
              "verified_purchase": False, "helpful_vote": 0}
    rows[0].update(fields)
    reviews.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    run(tmp_path, meta, reviews)
    saved = [json.loads(line) for line in (tmp_path / "result/laptop_valid.jsonl").read_text().splitlines()]
    for key, value in fields.items():
        assert saved[0]["review_title" if key == "title" else key] == value
    assert saved[0]["text"] == rows[0]["text"]
    assert saved[1]["user_id"] is saved[1]["review_title"] is None


def test_process_memory_failure_is_reported(tmp_path, monkeypatch):
    meta, reviews = inputs(tmp_path)
    monkeypatch.setattr("src.data.feasibility.process_memory", lambda: {"working_set_bytes": 10**9})
    with pytest.raises(MemoryError):
        run(tmp_path, meta, reviews)
    diagnostic = json.loads((tmp_path / "result/failure.json").read_text())
    assert diagnostic["metadata_scan"]["stop_reason"] == "memory_limit"


def test_review_output_limit_is_reported(tmp_path):
    meta, reviews = inputs(tmp_path)
    config = copy.deepcopy(load_config("feasibility"))
    config["limits"]["max_probe_output_bytes"] = 650
    result = run(tmp_path, meta, reviews, config)
    assert result["review_scan"]["stop_reason"] == "output_limit"
    assert not result["source_coverage_complete"]


def test_model_only_title_stays_excluded_baseline_but_enters_boundary_qa(tmp_path):
    meta, reviews = inputs(tmp_path)
    meta.write_text(json.dumps(product("l", "ThinkPad X1 Carbon", ["Laptops"])) + "\n", encoding="utf-8")
    result = run(tmp_path, meta, reviews)
    assert result["groups"]["laptop"]["candidate_products"] == 0
    qa = next((tmp_path / "qa").glob("*laptop*.csv"))
    row = next(csv.DictReader(qa.open(encoding="utf-8-sig")))
    assert row["stratum"] == "excluded_near_boundary"
    assert row["human_is_target_product"] == ""


def test_metadata_preflight_requires_no_review_file(tmp_path):
    meta, reviews = inputs(tmp_path)
    complete_manifests(meta, reviews)
    result = run(tmp_path, meta, None, mode="scan", allow_large_scan=True, metadata_only=True)
    assert result["metadata_coverage_complete"] and result["status"] == "DONE"
    assert result["filter_decisions"]["laptop"]["laptop_category_and_title"] == 1
    assert result["filter_decisions"]["laptop"]["accessory_or_ambiguous_title"] == 1
    assert result["review_scan"]["stop_reason"] == "not_started"
    assert not result["source_coverage_complete"]
    assert run(tmp_path, meta, None, mode="scan", allow_large_scan=True, metadata_only=True) == result


def test_raw_input_and_annotation_directories_protected(tmp_path):
    meta, reviews = inputs(tmp_path)
    with pytest.raises(ValueError, match="separate"):
        run_feasibility(meta, reviews, tmp_path, tmp_path / "qa", load_config("feasibility"),
                        load_config("acquisition"), source="Fixture")


def test_mismatched_source_manifest_cannot_claim_complete_metadata(tmp_path):
    meta, reviews = inputs(tmp_path)
    complete_manifests(meta, reviews)
    with pytest.raises(ValueError, match="complete metadata"):
        run_feasibility(meta, reviews, tmp_path / "result", tmp_path / "qa",
                        load_config("feasibility"), load_config("acquisition"),
                        source="Electronics", mode="scan", allow_large_scan=True)
    diagnostic = json.loads((tmp_path / "result/failure.json").read_text())
    assert diagnostic["inputs"]["metadata"]["provenance"] == "source_url_mismatch_or_missing"


def test_convertible_not_rejected_by_other_domain_groups(tmp_path):
    meta, reviews = inputs(tmp_path)
    meta.write_text(json.dumps(product("l", "Laptop 2-in-1 with tablet mode", ["Computers & Tablets", "Laptops"])) + "\n", encoding="utf-8")
    result = run(tmp_path, meta, reviews)
    assert result["groups"]["laptop"]["candidate_products"] == 1
    assert result["groups"]["laptop"]["valid_reviews"] == 2


def test_corrupt_metadata_has_failure_report_without_reviews(tmp_path):
    meta, reviews = inputs(tmp_path)
    corrupt = tmp_path / "metadata.gz"
    corrupt.write_bytes(b"invalid gzip")
    with pytest.raises(ValueError, match="corrupt"):
        run(tmp_path, corrupt, reviews)
    diagnostic = json.loads((tmp_path / "result/failure.json").read_text())
    assert diagnostic["metadata_scan"]["stop_reason"] == "corrupt_source"
    assert diagnostic["review_scan"]["stop_reason"] == "not_started"


def test_manifest_checksum_mismatch_fails_before_outputs(tmp_path):
    meta, reviews = inputs(tmp_path)
    complete_manifests(meta, reviews)
    meta.write_text("tampered\n", encoding="utf-8")
    with pytest.raises(ValueError, match="checksum"):
        run(tmp_path, meta, reviews)
    assert not (tmp_path / "result").exists()


def test_non_laptop_group_rejected_before_source_access(tmp_path):
    config = copy.deepcopy(load_config("feasibility"))
    config["groups"] = ["tablet"]
    with pytest.raises(ValueError, match="laptop project domain"):
        run(tmp_path, tmp_path / "absent", tmp_path / "absent", config)


def test_active_source_and_language_scope():
    assert set(load_config("feasibility")["sources"]) == {"Electronics"}
    assert load_config("feasibility")["groups"] == ["laptop"]
    assert set(load_config("feasibility")["survey"]["aspect_keywords"]) == {"laptop"}
