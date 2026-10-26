"""Đồ đạc tổng hợp, không bao giờ là bộ gold do con người gán nhãn hoặc hiệu suất được đo thực tế."""

import json
from copy import deepcopy
from pathlib import Path

import pytest

from src.config import load_config
from src.data.acquisition import sha256_file
from src.data.independent_qa import (PRODUCT_COLUMNS, REVIEW_COLUMNS, HUMAN_COLUMNS,
                                    Reservoir, prepare_independent_qa, evaluate_independent_qa,
                                    fixed_fingerprint, read_csv, write_csv, write_evaluation)


def make_kit(path: Path):
    path.mkdir()
    private = []
    # Các quần thể tầng lớp không đồng đều phân biệt có trọng số với độ bao phủ (recall) được gộp chung ngây thơ.
    specifications = [("product", "random_keep", True, 100, "laptop"),
                      ("product", "diagnostic", False, 30, "laptop"),
                      ("review", "random_keep", True, 10, "laptop"),
                      ("review", "random_keep", True, 10, "non_laptop"),
                      ("review", "random_reject", False, 1000, "laptop"),
                      ("review", "random_reject", False, 1000, "non_laptop"),
                      ("review", "diagnostic", False, 200, "laptop")]
    for task in ("product", "review"):
        columns = PRODUCT_COLUMNS if task == "product" else REVIEW_COLUMNS
        rows = []
        for i, (kind, stratum, prediction, population, label) in enumerate(specifications):
            if kind != task:
                continue
            row = {k: "" for k in columns}
            row.update(annotation_id=str(i), product_id=f"product{i}", title="vật cố tổng hợp",
                       human_label=label, human_evidence="Synthetic fixture evidence; not real human label")
            rows.append(row)
            private.append({"annotation_id": str(i), "task": task, "stratum": stratum,
                            "prediction": prediction, "pipeline_reason": "fixture", "frame_population": population,
                            "sample_size": sum(t == task and s == stratum for t, s, *_ in specifications),
                            "fixed_fingerprint": fixed_fingerprint(row)})
        write_csv(path / f"{task}_annotation.csv", columns, rows)
    p = path / "private_predictions.json"
    p.write_text(json.dumps(private))
    (path / "manifest.json").write_text(json.dumps({"files": {p.name: {"sha256": sha256_file(p)}}, "scope": "fixture frames"}))
    return path


def evaluate(kit):
    return evaluate_independent_qa(kit, {t: kit / f"{t}_annotation.csv" for t in ("product", "review")},
                                   annotator="fixture human declaration", independent_human=True)


def test_ai_assistance_disclosed_without_changing_metrics_or_inputs(tmp_path):
    kit = make_kit(tmp_path / "kit")
    before = {p.name: p.read_bytes() for p in kit.iterdir()}
    result = evaluate_independent_qa(
        kit, {t: kit / f"{t}_annotation.csv" for t in ("product", "review")},
        annotator="fixture reviewer", independent_human=True, ai_assisted_review=True)
    assert result["label_provenance"] == "human_verified_after_ai_assistance"
    assert result["review_weighted_estimates"] == evaluate(kit)["review_weighted_estimates"]
    write_evaluation(result, tmp_path / "evaluation")
    assert "not fully blind" in (tmp_path / "evaluation/report.md").read_text()
    assert before == {p.name: p.read_bytes() for p in kit.iterdir()}


def edit_annotation(kit, mutate, task="review"):
    p = kit / f"{task}_annotation.csv"
    columns, rows = read_csv(p)
    mutate(rows)
    p.unlink()  # Chỉ thiết bị cố định do kiểm thử tạo ra.
    write_csv(p, columns, rows)


def test_weighted_review_estimates_and_diagnostic_exclusion(tmp_path):
    kit = make_kit(tmp_path / "kit")
    before = {p.name: p.read_bytes() for p in kit.iterdir()}
    result = evaluate(kit)
    metrics = result["review_weighted_estimates"]
    assert metrics["confusion_matrix"] == {"TP": 5, "FP": 5, "FN": 500, "TN": 500}
    assert metrics["precision"] == .5
    assert metrics["recall"] == pytest.approx(5 / 505)
    assert metrics["f1"] == pytest.approx(10 / 515)
    assert result["strata"]["product:random_keep"]["recall"] is None
    assert result["strata"]["product:random_keep"]["precision"] == 1
    assert result["strata"]["review:diagnostic"]["metrics"] is None
    write_evaluation(result, tmp_path / "evaluation")
    assert (tmp_path / "evaluation/report.md").exists()
    assert before == {p.name: p.read_bytes() for p in kit.iterdir()}
    with pytest.raises(FileExistsError):
        write_evaluation(result, tmp_path / "evaluation")


@pytest.mark.parametrize("label", ["", "uncertain"])
def test_unresolved_withholds_weighted_metrics_and_reports_bounds(tmp_path, label):
    kit = make_kit(tmp_path / "kit")
    edit_annotation(kit, lambda rows: rows[0].update(human_label=label))
    result = evaluate(kit)
    assert result["review_weighted_estimates"] is None
    assert result["pending_or_uncertain"] == 1
    assert result["strata"]["review:random_keep"]["laptop_fraction_bounds"] == [0, .5]


@pytest.mark.parametrize("mutation", ["id", "evidence", "label", "reason", "text", "duplicate", "missing"])
def test_reject_invalid_annotation_or_changed_identity(tmp_path, mutation):
    kit = make_kit(tmp_path / "kit")
    def mutate(rows):
        if mutation == "id": rows[0]["annotation_id"] = "wrong"
        if mutation == "evidence": rows[0]["human_evidence"] = ""
        if mutation == "label": rows[0]["human_label"] = "positive"
        if mutation == "reason": rows[0]["human_error_reason"] = "invented"
        if mutation == "text": rows[0]["review_text"] = "changed"
        if mutation == "duplicate": rows.append(deepcopy(rows[0]))
        if mutation == "missing": rows.pop()
    edit_annotation(kit, mutate)
    with pytest.raises(ValueError):
        evaluate(kit)


def test_explicit_human_declaration_and_private_integrity(tmp_path):
    kit = make_kit(tmp_path / "kit")
    with pytest.raises(ValueError, match="declaration"):
        evaluate_independent_qa(kit, {}, annotator="someone")
    (kit / "private_predictions.json").write_text("[]")
    with pytest.raises(ValueError, match="sidecar"):
        evaluate(kit)


def test_conflicting_product_labels_require_adjudication(tmp_path):
    kit = make_kit(tmp_path / "kit")
    # Chỉ gắn lại vật cố định tổng hợp, mô phỏng một sản phẩm lặp đi lặp lại trong bộ sản phẩm.
    edit_annotation(kit, lambda rows: rows[1].update(product_id="product2"))
    _, rows = read_csv(kit / "review_annotation.csv")
    private_path = kit / "private_predictions.json"
    private = json.loads(private_path.read_text())
    for ref in private:
        if ref["annotation_id"] == rows[1]["annotation_id"]:
            ref["fixed_fingerprint"] = fixed_fingerprint(rows[1])
    private_path.write_text(json.dumps(private))
    manifest_path = kit / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["files"][private_path.name]["sha256"] = sha256_file(private_path)
    manifest_path.write_text(json.dumps(manifest))
    result = evaluate(kit)
    assert result["conflicting_product_labels"] == ["product2"]
    assert result["review_weighted_estimates"] is None
    assert result["strata"]["product:random_keep"]["precision"] is None


@pytest.mark.parametrize("payload", ["a,a\n1,2\n", "a,b\n1\n", "a,b\n1,2,3\n", 'a,b\n"unfinished,2'])
def test_malformed_csv_boundaries(tmp_path, payload):
    path = tmp_path / "bad.csv"
    path.write_text(payload)
    with pytest.raises(ValueError):
        read_csv(path)


def test_reservoir_reproducible_and_unique():
    a, b = Reservoir(20, 42), Reservoir(20, 42)
    for i in range(1000):
        a.add({"id": i}); b.add({"id": i})
    assert a.rows == b.rows and a.count == 1000
    assert len({r["id"] for r in a.rows}) == 20


def test_preparation_end_to_end_fixture(tmp_path):
    raw, run = tmp_path / "raw", tmp_path / "run"
    raw.mkdir(); run.mkdir()
    acquisition = load_config("acquisition")
    products = [{"parent_asin": f"K{i}", "title": "Example Laptop", "categories": ["Laptops"]} for i in range(4)]
    excluded = [{"parent_asin": f"R{i}", "title": "Laptop sleeve", "categories": ["Laptop Accessories"]} for i in range(8)]
    meta = raw / "metadata.jsonl"
    meta.write_text("".join(json.dumps(r) + "\n" for r in products + excluded))
    rows = [{"parent_asin": f"K{i}" if i < 4 else f"R{i-4}", "text": "Fixture short text", "title": "Fixture review", "rating": 5} for i in range(12)]
    reviews = raw / "reviews.jsonl"
    reviews.write_text("".join(json.dumps(r) + "\n" for r in rows))
    inputs = {}
    for kind, path in (("metadata", meta), ("reviews", reviews)):
        manifest = {"sha256": sha256_file(path), "source_url": acquisition["amazon"][f"{kind}_url"], "complete_source": True}
        Path(str(path) + ".manifest.json").write_text(json.dumps(manifest))
        inputs[kind] = {"name": path.name, "sha256": manifest["sha256"]}
    (run / "products.jsonl").write_text("".join(json.dumps(r) + "\n" for r in products))
    saved = [{**r, "review_id": f"amazon2023:{inputs['reviews']['sha256']}:{i+1}", "source_line": i+1,
              "product_title": "Example Laptop", "review_title": r["title"]} for i, r in enumerate(rows[:4])]
    (run / "laptop_valid.jsonl").write_text("".join(json.dumps(r) + "\n" for r in saved))
    report = {"source": "Electronics", "source_coverage_complete": True, "inputs": inputs,
              "output_sha256": {p.name: sha256_file(p) for p in run.iterdir()},
              "groups": {"laptop": {"candidate_products": 4, "valid_reviews": 4, "matched_reviews": 4}},
              "review_scan": {"rows": 12}, "metadata_scan": {"rows": 12},
              "join_counts": {"not_in_selected_metadata_index": 8}}
    (run / "report.json").write_text(json.dumps(report))
    before = {p: p.read_bytes() for folder in (raw, run) for p in folder.iterdir()}
    result = prepare_independent_qa(run, raw, tmp_path / "kit1", acquisition, load_config("feasibility")["limits"], product_n=2, boundary_n=2, review_n=2, diagnostic_n=1)
    prepare_independent_qa(run, raw, tmp_path / "kit2", acquisition, load_config("feasibility")["limits"], product_n=2, boundary_n=2, review_n=2, diagnostic_n=1)
    assert result["samples"] == {"product:random_keep": 2, "product:diagnostic": 2, "review:random_keep": 2, "review:random_reject": 2, "review:diagnostic": 1}
    for task in ("product", "review"):
        columns, annotated = read_csv(tmp_path / f"kit1/{task}_annotation.csv")
        assert not {"prediction", "stratum", "pipeline_reason", "rule_include"} & set(columns)
        assert all(not r[c] for r in annotated for c in HUMAN_COLUMNS)
        assert (tmp_path / f"kit1/{task}_annotation.csv").read_bytes() == (tmp_path / f"kit2/{task}_annotation.csv").read_bytes()
    assert before == {p: p.read_bytes() for folder in (raw, run) for p in folder.iterdir()}
    with pytest.raises(FileExistsError):
        prepare_independent_qa(run, raw, tmp_path / "kit1", acquisition, load_config("feasibility")["limits"])
