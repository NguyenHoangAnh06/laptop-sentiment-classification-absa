"""Fixture tổng hợp cho cổng công khai, không chứa credentials hoặc corpus thật."""

import json
from pathlib import Path
import subprocess

from scripts.audit_public_snapshot import audit, corpus_findings, secret_findings


def test_token_is_reported_without_value() -> None:
    value = "gh" + "p_" + "a" * 36
    result = secret_findings("first\n" + value)
    assert result == [{"kind": "github_token", "line": 2}]
    assert value not in json.dumps(result)


def test_environment_access_is_not_literal_secret() -> None:
    assert secret_findings('token = os.environ["TABPFN_TOKEN"]') == []
    assert secret_findings('api_key = "your_placeholder_key_here"') == []


def test_original_text_is_distinct_from_metrics() -> None:
    assert corpus_findings(Path("metrics.json"), '{"text": {"rows": 30}, "examples": 10}') == []
    assert corpus_findings(Path("examples.json"), '{"text": "Synthetic fixture sentence with six distinct words."}') == ["corpus_json_string"]
    assert corpus_findings(Path("examples.csv"), "review_id,text\nfixture,Synthetic\n") == ["corpus_csv_columns"]


def test_notebook_outputs_require_review() -> None:
    assert corpus_findings(Path("source.ipynb"), '{"cells": [{"outputs": []}]}') == []
    assert corpus_findings(Path("executed.ipynb"), '{"cells": [{"outputs": [{"text": "fixture"}]}]}') == ["notebook_outputs_review"]


def test_ignore_does_not_hide_candidate_blockers(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    (tmp_path / ".gitignore").write_text("*.pt\n.env\n", encoding="utf-8")
    (tmp_path / "weights.pt").write_bytes(b"fixture")
    (tmp_path / ".env").write_text("FIXTURE_ONLY=true", encoding="utf-8")
    (tmp_path / "leaked.npy").write_bytes(b"fixture")
    (tmp_path / "reports").mkdir()
    (tmp_path / "reports" / "examples.csv").write_text("review_id,text\nfake,Synthetic\n", encoding="utf-8")
    result = audit(tmp_path)
    assert set(result["candidate_blockers"]) == {"leaked.npy", "reports/examples.csv"}
    assert result["secret_scan"] == "PASS"
    ignored = {r["path"] for r in result["records"] if r["ignored"]}
    assert {".env", "weights.pt"} <= ignored


def test_utf16_log_is_scanned(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    value = "hf" + "_" + "b" * 32
    (tmp_path / "run.log").write_text(value, encoding="utf-16")
    result = audit(tmp_path)
    assert result["secret_scan"] == "BLOCKED"
    assert result["candidate_blockers"] == ["run.log"]
    assert value not in json.dumps(result)
