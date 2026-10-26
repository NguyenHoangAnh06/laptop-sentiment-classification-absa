"""Truyền trực tuyến trình đọc nguồn; không có phép biến đổi thô hoặc phỏng đoán lược đồ."""

import gzip
import json
import time
import zlib
from dataclasses import dataclass, field
from pathlib import Path
from collections.abc import Iterator, Mapping


def iter_jsonl(path: Path) -> Iterator[tuple[int, dict]]:
    """Số dòng nguồn và đối tượng năng suất; thất bại rõ ràng trên các bản ghi không đúng định dạng."""
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                raise ValueError(f"{path.name}:{line_number}: blank JSONL record")
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path.name}:{line_number}: invalid JSON") from exc
            if not isinstance(row, dict):
                raise ValueError(f"{path.name}:{line_number}: expected object")
            yield line_number, row


def first_present(row: Mapping, aliases: list[str], required: bool = False):
    """Giải quyết các bí danh đã khai báo; từ chối các giá trị không null xung đột."""
    values = [row[key] for key in aliases if key in row and row[key] is not None]
    if any(value != values[0] for value in values[1:]):
        raise ValueError(f"Conflicting schema aliases: {aliases}")
    if not values or values[0] == "":
        if required:
            raise ValueError(f"Missing required field: {aliases}")
        return None
    return values[0]


@dataclass
class ScanStats:
    rows: int = 0
    decoded_bytes: int = 0
    invalid_records: int = 0
    oversized_records: int = 0
    malformed_records: int = 0
    truncated_records: int = 0
    eof_observed: bool = False
    stop_reason: str = "source_eof"
    error_lines: list[int] = field(default_factory=list)


def scan_jsonl(path: Path, stats: ScanStats, *, max_rows: int,
               max_bytes: int, deadline: float, max_record_bytes: int = 1_000_000) -> Iterator[tuple[int, dict]]:
    """Bỏ qua các dòng vật lý quá khổ trong các phần giới hạn; không bao giờ phân tích đuôi của họ.

    JSON cuối cùng không hợp lệ nếu không có dòng mới được báo cáo là bản ghi bị nghi ngờ bị cắt bớt. JSON hợp lệ tại EOF không có dòng mới được chấp nhận. Lỗi GZIP không thành công. EOF đề cập đến tệp cục bộ, độc lập với tính đầy đủ của bản kê nguồn.
    """
    if min(max_rows, max_bytes, max_record_bytes) <= 0:
        raise ValueError("Scan budgets must be positive")
    opener = gzip.open if path.suffix == ".gz" else open
    try:
        with opener(path, "rb") as handle:
            while True:
                if time.monotonic() >= deadline:
                    stats.stop_reason = "time_limit"
                    return
                if stats.rows >= max_rows:
                    stats.stop_reason = "record_limit"
                    return
                if stats.decoded_bytes >= max_bytes:
                    stats.stop_reason = "byte_limit"
                    return
                remaining = max_bytes - stats.decoded_bytes
                line = handle.readline(min(max_record_bytes + 1, remaining))
                if not line:
                    stats.eof_observed = True
                    return
                stats.decoded_bytes += len(line)
                if len(line) > max_record_bytes:
                    stats.rows += 1
                    stats.invalid_records += 1
                    stats.oversized_records += 1
                    if len(stats.error_lines) < 20:
                        stats.error_lines.append(stats.rows)
                    while not line.endswith(b"\n"):
                        if time.monotonic() >= deadline:
                            stats.stop_reason = "time_limit"
                            return
                        remaining = max_bytes - stats.decoded_bytes
                        if remaining <= 0:
                            stats.stop_reason = "byte_limit"
                            return
                        line = handle.readline(min(65536, remaining))
                        stats.decoded_bytes += len(line)
                        if not line:
                            stats.truncated_records += 1
                            stats.eof_observed = True
                            return
                    continue
                if len(line) == remaining and not line.endswith(b"\n"):
                    stats.stop_reason = "byte_limit"
                    return
                stats.rows += 1
                try:
                    row = json.loads(line)
                    if not isinstance(row, dict):
                        raise ValueError("Non-object JSON")
                except (ValueError, UnicodeDecodeError):
                    stats.invalid_records += 1
                    if not line.endswith(b"\n"):
                        stats.truncated_records += 1
                    else:
                        stats.malformed_records += 1
                    if len(stats.error_lines) < 20:
                        stats.error_lines.append(stats.rows)
                    continue
                yield stats.rows, row
    except (OSError, EOFError, zlib.error) as exc:
        stats.stop_reason = "corrupt_source"
        raise ValueError(f"Unreadable/corrupt source: {path.name}") from exc
