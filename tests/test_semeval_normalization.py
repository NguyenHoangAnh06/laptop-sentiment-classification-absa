"""Chỉ đồ đạc tổng hợp; bằng chứng thực tế tồn tại trong báo cáo chuẩn hóa."""

import json
import pytest

from src.data.semeval import read_semeval_sentences, validate_semeval_sentences, normalize_semeval, write_semeval_jsonl


def fixture(path):
    path.write_text('<sentences><sentence id="001"><text>screen good battery bad</text><aspectTerms>'
                    '<aspectTerm term="screen" from="0" to="6" polarity="positive"/>'
                    '<aspectTerm term="battery" from="12" to="19" polarity="conflict"/>'
                    '</aspectTerms></sentence><sentence id="002"><text>Fine &amp; OK.</text></sentence>'
                    '<sentence id="003"><text></text></sentence></sentences>', encoding="utf-8")
    return path


def test_roundtrip_counts_splits_conflict_and_determinism(tmp_path):
    paths = {s: fixture(tmp_path / f"{s}.xml") for s in ("train", "test")}
    before = {s: p.read_bytes() for s, p in paths.items()}
    result = normalize_semeval(paths, tmp_path / "out")
    output = tmp_path / "out/train_sentences.jsonl"
    first = output.read_bytes()
    normalize_semeval(paths, tmp_path / "out")
    assert output.read_bytes() == first
    rows = [json.loads(line) for line in output.read_text().splitlines()]
    assert rows[0]["sentence_id"] == "001"
    assert rows[0]["aspects"][1]["polarity"] == "conflict"
    assert rows[1]["text"] == "Fine & OK." and rows[1]["aspects"] == []
    assert rows[2]["text"] == ""
    assert all(r["split"] == "train" for r in rows)
    assert result["splits"]["train"]["input"]["records"] == len(rows) == 3
    assert result["splits"]["train"]["aspect_terms"] == 2
    assert result["train_test_overlap"]["exact_text_test_ids"] == ["001", "002", "003"]
    assert {s: p.read_bytes() for s, p in paths.items()} == before
    with pytest.raises(FileExistsError):
        write_semeval_jsonl(output, [])


def test_diagnostics_keep_invalid_spans_and_labels(tmp_path):
    path = fixture(tmp_path / "bad.xml")
    path.write_text(path.read_text().replace('from="12"', 'from="bad"').replace('polarity="conflict"', 'polarity="unknown"').replace('id="002"', 'id="001"'))
    rows = read_semeval_sentences(path, "test")
    audit = validate_semeval_sentences(rows)
    assert audit["duplicate_ids"] == {"001": 2}
    assert {d["kind"] for d in audit["diagnostics"]} == {"invalid_span", "unsupported_or_missing_polarity", "empty_text"}
    assert rows[0]["aspects"][1]["start"] == "bad"


@pytest.mark.parametrize("xml", ["<sentences>", "<sentences/>", '<sentences><sentence id="a"><text>x</text><extra/></sentence></sentences>'])
def test_unreadable_or_unrepresented_schema_fails(tmp_path, xml):
    path = tmp_path / "bad.xml"
    path.write_text(xml)
    with pytest.raises(Exception):
        read_semeval_sentences(path, "train")
