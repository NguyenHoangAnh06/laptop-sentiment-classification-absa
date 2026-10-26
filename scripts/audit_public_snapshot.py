"""Kiểm kê snapshot Git công khai; không stage, commit hoặc in giá trị secret."""

from __future__ import annotations

import argparse
import csv
from datetime import datetime
import io
import json
import os
from pathlib import Path
import re
import subprocess
from zoneinfo import ZoneInfo


TOKEN_PATTERNS = {
    "github_token": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b"),
    "huggingface_token": re.compile(r"\bhf_[A-Za-z0-9]{30,}\b"),
    "api_key": re.compile(r"\b(?:sk-(?:proj-)?[A-Za-z0-9_-]{24,}|AKIA[A-Z0-9]{16})\b"),
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "url_credential": re.compile(r"https?://[^\s/:@]+:[^\s/@]+@|[?&](?:access_token|api_key|token)=[A-Za-z0-9_.-]{12,}", re.I),
    "literal_credential": re.compile(
        r'''(?i)["']?(?:TABPFN_TOKEN|HF_TOKEN|GITHUB_TOKEN|KAGGLE_KEY|api_key|password|access_token)["']?\s*[:=]\s*["']([A-Za-z0-9_./+!=-]{16,})["']'''
    ),
}
TEXT_EXTENSIONS = {".py", ".yaml", ".yml", ".json", ".jsonl", ".csv", ".md", ".txt", ".log", ".ipynb", ".html", ".svg", ".ini", ".toml", ".cfg", ".sh", ".ps1"}
FORBIDDEN_EXTENSIONS = {".safetensors", ".bin", ".pt", ".pth", ".joblib", ".ubj", ".npy", ".npz", ".parquet", ".gz", ".zip", ".sqlite", ".xml"}
CORPUS_FIELDS = {"text", "review_text", "review_title", "text_excerpt", "snippet", "sentence", "body"}


def secret_findings(text: str) -> list[dict]:
    """Chỉ trả loại rủi ro và dòng; không lưu nội dung khớp."""
    findings = []
    for kind, pattern in TOKEN_PATTERNS.items():
        for match in pattern.finditer(text):
            if kind == "literal_credential" and any(x in match.group(1).lower() for x in ("example", "placeholder", "your_", "redacted")):
                continue
            findings.append({"kind": kind, "line": text.count("\n", 0, match.start()) + 1})
    return findings


def corpus_findings(path: Path, text: str) -> list[str]:
    """Phân biệt payload văn bản gốc với số đếm/lược đồ cùng tên khóa."""
    findings = set()
    if path.suffix == ".csv":
        headers = next(csv.reader(io.StringIO(text)), [])
        if CORPUS_FIELDS.intersection(headers):
            findings.add("corpus_csv_columns")
    elif path.suffix == ".json":
        def visit(value: object) -> None:
            if isinstance(value, dict):
                for key, item in value.items():
                    if key in CORPUS_FIELDS and isinstance(item, str) and len(item.split()) >= 6:
                        findings.add("corpus_json_string")
                    visit(item)
            elif isinstance(value, list):
                for item in value:
                    visit(item)
        visit(json.loads(text))
    elif path.suffix == ".ipynb":
        if any(cell.get("outputs") for cell in json.loads(text).get("cells", [])):
            findings.add("notebook_outputs_review")
    return sorted(findings)


def audit(root: Path) -> dict:
    """Duyệt mọi file ngoài Git internals; cache/môi trường chỉ kiểm kê metadata."""
    paths = []
    for base, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d != ".git")
        paths.extend((Path(base) / name).relative_to(root).as_posix() for name in sorted(files))
    ignored_result = subprocess.run(
        ["git", "check-ignore", "--no-index", "-z", "--stdin"], cwd=root,
        input="\0".join(paths) + "\0", text=True, capture_output=True, check=False,
    )
    if ignored_result.returncode not in (0, 1):
        raise RuntimeError("git check-ignore thất bại")
    ignored = set(ignored_result.stdout.rstrip("\0").split("\0"))
    records = []
    for name in paths:
        path = root / name
        size = path.stat().st_size
        is_ignored = name in ignored
        flags = []
        secrets = []
        parts = Path(name).parts
        metadata_only = any(p in {".venv", "__pycache__", ".pytest_cache", ".qodo"} for p in parts)
        if path.is_symlink():
            flags.append("symlink_review")
        credential_name = path.name.lower()
        if not metadata_only and ((credential_name.startswith(".env") and credential_name != ".env.example") or credential_name in {"kaggle.json", "credentials.json", "id_rsa", "id_ed25519", ".netrc", ".pypirc"} or path.suffix in {".pem", ".key", ".p12"}):
            secrets.append({"kind": "credential_filename", "line": None})
        scan_text = not metadata_only and parts[0] != "data" and not name.startswith("reports/github_publication_local/") and (path.suffix in TEXT_EXTENSIONS or path.name.startswith(".env") or not path.suffix) and size <= 10_000_000 and not path.is_symlink()
        if scan_text:
            try:
                raw = path.read_bytes()
                content = raw.decode("utf-16" if raw.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8-sig")
            except UnicodeError:
                flags.append("encoding_review")
            else:
                secrets.extend(secret_findings(content))
                if parts[0] in {"reports", "notebooks", "cloud"}:
                    try:
                        flags.extend(corpus_findings(path, content))
                    except (ValueError, csv.Error):
                        flags.append("parse_review")
                if re.search(r"[Cc]:[/\\]+Users[/\\]+ADMIN", content):
                    flags.append("historical_local_path_review")
        if size > 10_000_000:
            flags.append("large_file")
        forbidden = path.suffix.lower() in FORBIDDEN_EXTENSIONS or (parts[0] in {"data", "artifacts"} and path.name != ".gitkeep")
        if forbidden:
            flags.append("dataset_model_or_binary")
        category = "IGNORE" if is_ignored else "TRACK"
        if secrets:
            category = "SECRET RISK"
        elif not is_ignored and size > 10_000_000:
            category = "LARGE FILE"
        elif not is_ignored and any(f != "historical_local_path_review" for f in flags):
            category = "REVIEW"
        records.append({"path": name, "bytes": size, "category": category, "ignored": is_ignored, "flags": flags, "secrets": secrets, "text_scanned": scan_text})
    summaries = {}
    for category in ["TRACK", "IGNORE", "REVIEW", "LARGE FILE", "SECRET RISK"]:
        selected = [r for r in records if r["category"] == category]
        summaries[category] = {"count": len(selected), "bytes": sum(r["bytes"] for r in selected)}
    candidates = [r for r in records if not r["ignored"]]
    blockers = [r["path"] for r in candidates if r["category"] != "TRACK"]
    return {"task_id": "GITHUB-PUBLISH-01", "date": datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).date().isoformat(), "timezone": "Asia/Saigon", "summary": summaries,
            "candidate_count": len(candidates), "candidate_bytes": sum(r["bytes"] for r in candidates),
            "candidate_blockers": blockers, "secret_scan": "PASS" if not any(r["secrets"] for r in candidates) else "BLOCKED",
            "scan_scope": "UTF-8/UTF-16-BOM text <=10MB, first-party files including ignored reports; data/, local audit inventory, venv/cache/binary datasets/models metadata-only. Heuristic scan, not proof of absence.",
            "large_files": [{"path": r["path"], "bytes": r["bytes"], "ignored": r["ignored"], "tier": ">=100MB" if r["bytes"] >= 100_000_000 else ">50MB" if r["bytes"] > 50_000_000 else ">10MB"} for r in records if r["bytes"] > 10_000_000],
            "records": records}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="Inventory local, không chứa giá trị secret")
    args = parser.parse_args()
    result = audit(Path.cwd())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k not in {"records", "large_files"}}, ensure_ascii=False, indent=2))
    raise SystemExit(1 if result["candidate_blockers"] else 0)


if __name__ == "__main__":
    main()
