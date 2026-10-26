"""Việc mua lại nguồn công cộng có giới hạn với các tệp và nguồn gốc bất biến."""

import gzip
import hashlib
import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def manifest_path(destination: Path) -> Path:
    """Ưu tiên một sidecar chỉnh sửa rõ ràng mà không làm thay đổi nguồn gốc ban đầu."""
    corrected = destination.with_suffix(destination.suffix + ".verified.manifest.json")
    return corrected if corrected.exists() else destination.with_suffix(destination.suffix + ".manifest.json")


def acquire(url: str, destination: Path, *, limit: int | None = None,
            max_bytes: int = 150_000_000, max_seconds: int = 180) -> dict:
    """Lưu trữ các dòng nguồn JSONL không thay đổi hoặc một tệp hoàn chỉnh nhỏ; không bao giờ ghi đè lên bản thô."""
    if max_bytes <= 0 or max_seconds <= 0 or (limit is not None and limit <= 0):
        raise ValueError("Acquisition budgets and record limit must be positive")
    manifest = manifest_path(destination)
    if destination.exists():
        if not manifest.exists():
            raise ValueError(f"Existing raw file has no manifest: {destination}")
        info = json.loads(manifest.read_text(encoding="utf-8"))
        if info["sha256"] != sha256_file(destination) or info["source_url"] != url or info["requested_limit"] != limit:
            raise ValueError("Raw checksum/source/limit mismatch; choose a new destination")
        return info
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp = destination.with_suffix(destination.suffix + ".partial")
    if temp.exists() or manifest.exists():
        raise ValueError(f"Existing partial/manifest requires inspection: {destination}")
    started = time.monotonic()
    rows = size = 0
    stop_reason = "source_eof"
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "laptop-review-research/0.1"})
        with urllib.request.urlopen(request, timeout=30) as response, temp.open("xb") as output:
            # Tiền tố JSONL giới hạn được giải mã từ gzip; tải xuống hoàn chỉnh
            # giữ nguyên các byte nén ban đầu khi nhận được.
            stream = gzip.GzipFile(fileobj=response) if limit is not None and url.endswith(".gz") else response
            while True:
                if time.monotonic() - started > max_seconds:
                    stop_reason = "time_limit"
                    break
                if limit is not None and rows >= limit:
                    stop_reason = "record_limit"
                    break
                block = stream.readline(max_bytes - size + 1) if limit is not None else stream.read(min(65536, max_bytes - size + 1))
                if not block:
                    break
                if size + len(block) > max_bytes:
                    if limit is None:
                        raise ValueError("Complete-file byte budget exceeded")
                    stop_reason = "byte_limit"
                    break
                if limit is not None:
                    if not isinstance(json.loads(block), dict):
                        raise ValueError("Source JSONL record is not an object")
                    rows += 1
                output.write(block)
                size += len(block)
            if limit is None and stop_reason != "source_eof":
                raise ValueError("Complete-file download timed out")
            length = response.headers.get("Content-Length")
            if limit is None and length is not None and size != int(length):
                raise ValueError("Incomplete HTTP body; full file not finalized")
            info = {
                "source_url": url, "resolved_url": response.url,
                "retrieved_utc": datetime.now(timezone.utc).isoformat(),
                "etag": response.headers.get("ETag"),
                "last_modified": response.headers.get("Last-Modified"),
                "requested_limit": limit, "rows": rows if limit is not None else None,
                "bytes": size, "stop_reason": stop_reason,
                "complete_source": stop_reason == "source_eof",
                "format": "unchanged_source_jsonl_lines" if limit else "original_file_bytes",
                "http_resume_implemented": False,
            }
        # Chỉ băm sau khi tay cầm đầu ra đã được xóa và đóng.
        info["sha256"] = sha256_file(temp)
        temp.rename(destination)
        manifest.write_text(json.dumps(info, indent=2) + "\n", encoding="utf-8")
        return info
    except Exception as exc:
        # Giữ một phần tập tin để chẩn đoán; các tập tin thô đã được hoàn thiện vẫn không thay đổi được.
        failure = temp.with_suffix(temp.suffix + ".failure.json")
        if temp.exists() and not failure.exists():
            failure.write_text(json.dumps({"source_url": url, "error_type": type(exc).__name__,
                                           "partial_sha256": sha256_file(temp), "partial_bytes": temp.stat().st_size,
                                           "finalized": False, "resume_supported": False}, indent=2) + "\n", encoding="utf-8")
        raise
