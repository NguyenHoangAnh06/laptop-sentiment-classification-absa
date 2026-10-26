"""Các thiết bị tổng hợp nhỏ cho logic P1; không bao giờ được sử dụng làm bằng chứng khoa học."""

import io
import json
import gzip
import urllib.request

import pytest

from src.config import load_config
from src.data.acquisition import acquire, sha256_file
from src.data.laptop_filter import classify_product, parent_identifier
from src.data.loader import first_present, iter_jsonl
from src.data.semeval import parse_semeval
from src.data.validation import SchemaProfile, deterministic_sample, sample_reviews
from src.data.filter_qa import validate_filter_qa


def product(title="Example Laptop", categories=None):
    return {"parent_asin": "fixture-parent", "title": title,
            "categories": categories if categories is not None else ["Electronics", "Computers & Accessories", "Laptops", "Traditional Laptops"]}


@pytest.mark.parametrize("title,categories,included", [
    ("Example Laptop", None, True), ("Example Chromebook", None, True),
    ("Laptop Bag", None, False), ("Laptop Charger", None, False),
    ("Laptop sleeve", None, False), ("Laptop docking station", None, False),
    ("Laptop replacement screen", None, False), ("Notebook stand", None, False),
    ("Example Laptop", ["Electronics", "Laptop Accessories"], False),
    ("Tablet", ["Electronics", "Tablets"], False),
    ("Laptop-compatible phone", ["Cell Phones"], False),
    ("Example Laptop", [], False),
])
def test_metadata_only_laptop_filter(title, categories, included):
    row = product(title, categories)
    row.update(text="laptop laptop", rating=5)
    assert classify_product(row, load_config("acquisition")["filter"]).include is included


@pytest.mark.parametrize("identifier", [None, "", "  ", 123])
def test_missing_identifiers_rejected(identifier):
    with pytest.raises(ValueError):
        parent_identifier({"parent_asin": identifier, "asin": "do-not-fallback"}, ["parent_asin"])


def test_schema_aliases_and_missing():
    assert first_present({"reviewText": "fixture"}, ["text", "reviewText"]) == "fixture"
    assert first_present({"helpful_votes": 0}, ["helpful_vote", "helpful_votes"]) == 0
    assert first_present({}, ["timestamp"]) is None
    with pytest.raises(ValueError):
        first_present({}, ["rating"], required=True)
    with pytest.raises(ValueError):
        first_present({"rating": 5, "overall": 1}, ["rating", "overall"])


def test_profile_counts_missing_null_and_types():
    profile = SchemaProfile()
    for row in ({"rating": 1, "text": None}, {"rating": 5.0}, {"rating": 3, "text": "fixture"}):
        profile.add(row)
    stats = profile.to_dict()
    assert stats["rows"] == 3
    assert stats["fields"]["text"]["absent"] == 1
    assert stats["fields"]["text"]["null"] == 1
    assert stats["fields"]["rating"]["types"] == {"int": 2, "float": 1}


def test_streaming_jsonl_and_invalid_records(tmp_path):
    path = tmp_path / "fixture.jsonl.gz"
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        handle.write('{"parent_asin":"fixture"}\n')
    assert list(iter_jsonl(path)) == [(1, {"parent_asin": "fixture"})]
    path = tmp_path / "invalid.jsonl"
    path.write_text("[]\n", encoding="utf-8")
    with pytest.raises(ValueError, match="expected object"):
        list(iter_jsonl(path))


def test_sampling_is_order_independent_and_preserves_strata_products():
    rows = [{"review_id": str(i), "rating": 1 if i < 8 else 5, "parent_asin": str(i % 2)} for i in range(10)]
    sample = sample_reviews(rows, 5, 42)
    assert sample == sample_reviews(list(reversed(rows)), 5, 42)
    assert len({row["review_id"] for row in sample}) == 5
    assert sum(row["rating"] == 1 for row in sample) == 4
    assert {row["parent_asin"] for row in sample} == {"0", "1"}
    assert deterministic_sample(rows, 3, 42) == deterministic_sample(reversed(rows), 3, 42)
    assert len(sample_reviews(rows, 50000, 42)) == len(rows)
    assert sample_reviews([], 5, 42) == []


def test_semeval_spans_polarities_and_original_split(tmp_path):
    path = tmp_path / "fixture.xml"
    path.write_text('<sentences><sentence id="fixture"><text>screen good battery bad</text><aspectTerms>'
                    '<aspectTerm term="screen" polarity="positive" from="0" to="6"/>'
                    '<aspectTerm term="battery" polarity="conflict" from="12" to="19"/>'
                    '</aspectTerms></sentence></sentences>', encoding="utf-8")
    parsed = parse_semeval(path, "train")[0]
    assert parsed["original_split"] == "train"
    assert parsed["aspects"][1]["original_polarity"] == "conflict"
    assert parsed["aspects"][1]["sentiment"] is None
    assert parsed["aspects"][1]["use_for_sentiment"] is False
    path.write_text(path.read_text().replace('from="12"', 'from="11"'), encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid aspect span"):
        parse_semeval(path, "test")


def test_acquisition_unchanged_prefix_and_idempotence(tmp_path, monkeypatch):
    original = b'{"parent_asin": "fixture-a"}\n{"parent_asin":"fixture-b"}\n'

    class Response(io.BytesIO):
        headers = {"ETag": "fixture-etag"}
        url = "https://fixture.invalid/data.gz"

    monkeypatch.setattr(urllib.request, "urlopen", lambda *args, **kwargs: Response(gzip.compress(original)))
    path = tmp_path / "snapshot.jsonl"
    info = acquire("https://fixture.invalid/data.gz", path, limit=1)
    assert path.read_bytes() == original.splitlines(keepends=True)[0]
    assert info["rows"] == 1 and info["complete_source"] is False
    assert acquire("https://fixture.invalid/data.gz", path, limit=1) == info
    assert info["sha256"] == sha256_file(path)
    path.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="mismatch"):
        acquire("https://fixture.invalid/data.gz", path, limit=1)


def test_human_qa_stays_unvalidated_until_complete(tmp_path):
    path = tmp_path / "fixture_qa.csv"
    header = "parent_asin,rule_include,human_is_laptop,human_notes\n"
    path.write_text(header + "a,True,,\nb,False,no,\n", encoding="utf-8")
    assert validate_filter_qa(path, minimum_included=1)["status"] == "unvalidated"
    path.write_text(header + "a,True,yes,fixture human label\nb,False,no,fixture human label\n", encoding="utf-8")
    assert validate_filter_qa(path, minimum_included=1)["observed_precision"] == 1.0
    assert validate_filter_qa(path, minimum_included=50)["status"] == "unvalidated"
    path.write_text(header + "a,True,unsure,\nb,False,no,\n", encoding="utf-8")
    assert validate_filter_qa(path, minimum_included=1)["observed_precision"] is None


def test_complete_gzip_download_preserves_compressed_source(tmp_path, monkeypatch):
    compressed = gzip.compress(b'{"fixture": true}\n')

    class Response(io.BytesIO):
        headers = {}
        url = "https://fixture.invalid/full.gz"

    monkeypatch.setattr(urllib.request, "urlopen", lambda *args, **kwargs: Response(compressed))
    path = tmp_path / "full.jsonl.gz"
    info = acquire("https://fixture.invalid/full.gz", path, max_bytes=1000)
    assert path.read_bytes() == compressed
    assert info["sha256"] == sha256_file(path)
    assert info["complete_source"] is True
