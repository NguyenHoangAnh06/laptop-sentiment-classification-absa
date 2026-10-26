"""Giữ nguyên ID câu SemEval gốc, phân chia nhãn, độ lệch và phân cực."""

import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
import json
from datetime import datetime, timezone

from src.data.acquisition import sha256_file


TRANSFORM_VERSION = "semeval_sentences_v1"
PROVENANCE = "User-supplied GitHub mirror files for personal study; dataset licence not officially verified; local SHA256 does not authenticate official origin."


def read_semeval_sentences(path: Path, split: str) -> list[dict]:
    """Đọc lossless mà không cần sửa chữa nhãn gán; từ chối lược đồ XML không được hỗ trợ."""
    if split not in {"train", "test"}:
        raise ValueError("Expected original train or test split")
    root = ET.parse(path).getroot()
    allowed = {"sentences": set(), "sentence": {"id"}, "text": set(),
               "aspectTerms": set(), "aspectTerm": {"term", "from", "to", "polarity"}}
    children = {"sentences": {"sentence"}, "sentence": {"text", "aspectTerms"},
                "text": set(), "aspectTerms": {"aspectTerm"}, "aspectTerm": set()}
    if root.tag != "sentences":
        raise ValueError("Expected sentences root")
    for element in root.iter():
        if (element.tag not in allowed or set(element.attrib) - allowed[element.tag]
                or any(child.tag not in children[element.tag] for child in element)):
            raise ValueError(f"Unsupported XML schema at {element.tag}; preserve raw and review")
    rows = []
    for sentence in root:
        if len(sentence.findall("text")) != 1 or len(sentence.findall("aspectTerms")) > 1:
            raise ValueError("Ambiguous sentence schema")
        aspects = []
        for aspect in sentence.findall("aspectTerms/aspectTerm"):
            attributes = dict(aspect.attrib)
            def offset(key: str):
                value = attributes.get(key)
                try:
                    return int(value)
                except (ValueError, TypeError):
                    return value
            aspects.append({"term": attributes.get("term"), "start": offset("from"),
                            "end": offset("to"), "polarity": attributes.get("polarity"),
                            "xml_attributes": attributes})
        rows.append({"source": "semeval2014_laptop", "split": split,
                     "sentence_id": sentence.get("id"), "text": sentence.findtext("text"),
                     "aspects": aspects})
    if not rows:
        raise ValueError("Empty SemEval file")
    return rows


def validate_semeval_sentences(rows: list[dict]) -> dict:
    """Thu thập tất cả các chẩn đoán gán nhãn, giữ lại mọi bản ghi gốc."""
    diagnostics = []
    def issue(index, row, kind, **details):
        diagnostics.append({"record_index": index, "sentence_id": row["sentence_id"],
                            "kind": kind, **details})
    for index, row in enumerate(rows):
        text = row["text"]
        if not row["sentence_id"]:
            issue(index, row, "missing_id")
        if not text:
            issue(index, row, "empty_text")
        for number, aspect in enumerate(row["aspects"]):
            start, end = aspect["start"], aspect["end"]
            if (not isinstance(start, int) or not isinstance(end, int) or not text
                    or not 0 <= start < end <= len(text) or text[start:end] != aspect["term"]):
                issue(index, row, "invalid_span", aspect_index=number, annotation=aspect,
                      observed=text[start:end] if isinstance(start, int) and isinstance(end, int) and text else None)
            if aspect["polarity"] not in {"positive", "negative", "neutral", "conflict"}:
                issue(index, row, "unsupported_or_missing_polarity", aspect_index=number, annotation=aspect)
            for previous in row["aspects"][:number]:
                if all(isinstance(v, int) for v in (start, end, previous["start"], previous["end"])) and max(start, previous["start"]) < min(end, previous["end"]):
                    issue(index, row, "overlapping_aspects", aspect_index=number)
    ids = Counter(r["sentence_id"] for r in rows)
    texts = Counter(r["text"] for r in rows)
    polarity = Counter(a["polarity"] for r in rows for a in r["aspects"])
    return {"sentences": len(rows), "aspect_terms": sum(polarity.values()),
            "sentences_with_aspects": sum(bool(r["aspects"]) for r in rows),
            "sentences_without_aspects": sum(not r["aspects"] for r in rows),
            "multiple_aspect_sentences": sum(len(r["aspects"]) > 1 for r in rows),
            "average_characters": sum(len(r["text"] or "") for r in rows) / len(rows),
            "average_whitespace_words": sum(len((r["text"] or "").split()) for r in rows) / len(rows),
            "polarities": dict(polarity), "duplicate_ids": {k: v for k, v in ids.items() if v > 1},
            "duplicate_text_groups": [{"text": k, "count": v} for k, v in texts.items() if v > 1],
            "diagnostics": diagnostics, "annotation_status": "PASS" if not diagnostics and all(v == 1 for v in ids.values()) else "REVIEW_REQUIRED"}


def write_semeval_jsonl(path: Path, rows: list[dict]) -> None:
    """Viết byte xác định; từ chối ghi đè lên dữ liệu khác hiện có."""
    payload = "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows).encode("utf-8")
    if path.exists():
        if path.read_bytes() != payload:
            raise FileExistsError(f"Different existing output: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(payload)


def normalize_semeval(paths: dict[str, Path], output_dir: Path) -> dict:
    """Chuẩn hóa các phân vùng ban đầu và xác minh các hàm băm thô và khứ hồi JSON đầy đủ."""
    if set(paths) != {"train", "test"}:
        raise ValueError("Both original train and test required")
    parsed = {split: read_semeval_sentences(path, split) for split, path in paths.items()}
    timestamp = datetime.now(timezone.utc).isoformat()
    report = {"transform_version": TRANSFORM_VERSION, "processing_timestamp": timestamp,
              "provenance": PROVENANCE, "splits": {}}
    for split, rows in parsed.items():
        path = paths[split]
        raw_hash = sha256_file(path)
        output = output_dir / f"{split}_sentences.jsonl"
        if output.resolve() in {p.resolve() for p in paths.values()} or "raw" in output.resolve().parts:
            raise ValueError("Output must not modify raw inputs")
        write_semeval_jsonl(output, rows)
        with output.open(encoding="utf-8") as handle:
            restored = [json.loads(line) for line in handle]
        if restored != rows or sha256_file(path) != raw_hash:
            raise ValueError("Integrity verification failed")
        def manifest(file, digest):
            return {"filename": file.as_posix(), "bytes": file.stat().st_size,
                    "sha256": digest, "records": len(rows), "aspect_terms": sum(len(r["aspects"]) for r in rows),
                    "status": "PASS", "processing_timestamp": timestamp,
                    "provenance": PROVENANCE, "transform_version": TRANSFORM_VERSION}
        report["splits"][split] = {**validate_semeval_sentences(rows),
                                   "input": manifest(path, raw_hash), "output": manifest(output, sha256_file(output)),
                                   "integrity": "PASS"}
    train, test = parsed["train"], parsed["test"]
    report["train_test_overlap"] = {
        "shared_sentence_ids": sorted({r["sentence_id"] for r in train} & {r["sentence_id"] for r in test}),
        "exact_text_test_ids": [r["sentence_id"] for r in test if r["text"] in {t["text"] for t in train}],
        "normalized_text_test_ids": [r["sentence_id"] for r in test if " ".join((r["text"] or "").casefold().split()) in {" ".join((t["text"] or "").casefold().split()) for t in train}],
        "policy": "Flag only; preserve original partitions. IDs are split-local. Do not train or tune on test."}
    return report


def parse_semeval(path: Path, split: str) -> list[dict]:
    """Xác thực chính xác căn chỉnh ký tự vị trí cụm từ; bảo quản conflict để chiết xuất."""
    if split not in {"train", "test", "trial"}:
        raise ValueError("SemEval split must be original train, test or trial")
    root = ET.parse(path).getroot()
    if root.tag != "sentences":
        raise ValueError("Expected SemEval sentences root")
    result, ids = [], set()
    for sentence in root.findall("sentence"):
        identifier, text = sentence.get("id"), sentence.findtext("text")
        if not identifier or identifier in ids or text is None:
            raise ValueError("Missing/duplicate sentence ID or missing text")
        ids.add(identifier)
        aspects = []
        for aspect in sentence.findall("aspectTerms/aspectTerm"):
            term, polarity = aspect.get("term"), aspect.get("polarity")
            start, end = int(aspect.get("from", "-1")), int(aspect.get("to", "-1"))
            if not term or not 0 <= start < end <= len(text) or text[start:end] != term:
                raise ValueError(f"Invalid aspect span in sentence {identifier}")
            if polarity not in {"negative", "neutral", "positive", "conflict"}:
                raise ValueError(f"Unsupported original polarity: {polarity}")
            aspects.append({"term": term, "from": start, "to": end, "original_polarity": polarity,
                            "sentiment": None if polarity == "conflict" else polarity,
                            "use_for_sentiment": polarity != "conflict"})
        result.append({"sentence_id": identifier, "text": text, "original_split": split, "aspects": aspects})
    if not result:
        raise ValueError("Empty SemEval file")
    return result


def audit_semeval_splits(paths: dict[str, Path]) -> dict:
    """Kiểm tra các tệp XML gốc một cách riêng biệt; chồng cờ mà không sửa đổi dữ liệu thô."""
    audits, parsed = {}, {}
    for split, path in paths.items():
        if split not in {"train", "test", "trial"}:
            raise ValueError("Unknown original split")
        if not path.exists():
            audits[split] = {"status": "missing", "path": path.as_posix()}
            continue
        rows = parse_semeval(path, split)
        parsed[split] = rows
        polarities = Counter(a["original_polarity"] for r in rows for a in r["aspects"])
        text_counts = Counter(r["text"] for r in rows)
        normalized_counts = Counter(" ".join(r["text"].casefold().split()) for r in rows)
        audits[split] = {"status": "audited", "path": path.as_posix(), "sha256": sha256_file(path),
                         "bytes": path.stat().st_size, "sentences": len(rows),
                         "aspect_terms": sum(polarities.values()), "polarities": dict(polarities),
                         "unsupported_labels": [], "conflict_terms": polarities["conflict"],
                         "sentences_without_aspects": sum(not r["aspects"] for r in rows),
                         "duplicate_text_additional_occurrences": sum(n - 1 for n in text_counts.values()),
                         "duplicate_normalized_text_additional_occurrences": sum(n - 1 for n in normalized_counts.values()),
                         "span_alignment": "PASS"}
    overlap = "NOT_MEASURED"
    if {"train", "test"}.issubset(parsed):
        train, test = parsed["train"], parsed["test"]
        train_ids = {r["sentence_id"] for r in train}
        train_texts = {r["text"] for r in train}
        normalized = {" ".join(r["text"].casefold().split()) for r in train}
        overlap = {"shared_sentence_ids": sorted(train_ids & {r["sentence_id"] for r in test}),
                   "test_sentences_with_exact_train_text": sum(r["text"] in train_texts for r in test),
                   "test_sentences_with_normalized_train_text": sum(" ".join(r["text"].casefold().split()) in normalized for r in test),
                   "note": "IDs are split-local; shared ID alone is not proof of identical text. Flag overlaps; preserve original partitions."}
    return {"status": "audited_original_splits" if {"train", "test"}.issubset(parsed) else "BLOCKED",
            "splits": audits, "train_test_overlap": overlap,
            "conflict_policy": "preserve_for_extraction_exclude_from_three_class_sentiment",
            "NEXT_ACTION": "Obtain authorized original Laptop train/test XML; trial is not a substitute" if overlap == "NOT_MEASURED" else "Review overlap flags before modeling"}
