"""Các bản ghi XML tổng hợp nhỏ dành cho kiểm tra split/overlap, không phải kết quả đánh giá so sánh."""

import pytest

from src.data.semeval import audit_semeval_splits, parse_semeval


def xml(path, sentence_id="a", text="screen good", polarity="positive"):
    path.write_text(f'<sentences><sentence id="{sentence_id}"><text>{text}</text>'
                    f'<aspectTerms><aspectTerm term="screen" from="0" to="6" polarity="{polarity}"/>'
                    '</aspectTerms></sentence></sentences>')
    return path


def test_original_splits_overlap_and_conflict_are_preserved(tmp_path):
    train = xml(tmp_path / "train.xml")
    test = xml(tmp_path / "test.xml", "b", polarity="conflict")
    before = train.read_bytes(), test.read_bytes()
    result = audit_semeval_splits({"train": train, "test": test})
    assert result["status"] == "audited_original_splits"
    assert result["splits"]["test"]["conflict_terms"] == 1
    assert result["train_test_overlap"]["test_sentences_with_exact_train_text"] == 1
    assert result["train_test_overlap"]["shared_sentence_ids"] == []
    assert (train.read_bytes(), test.read_bytes()) == before


def test_trial_cannot_satisfy_original_splits(tmp_path):
    result = audit_semeval_splits({"trial": xml(tmp_path / "trial.xml"),
                                  "train": tmp_path / "absent.xml", "test": tmp_path / "also_absent.xml"})
    assert result["status"] == "BLOCKED"
    assert result["train_test_overlap"] == "NOT_MEASURED"


def test_unsupported_polarity_not_silently_normalized(tmp_path):
    with pytest.raises(ValueError, match="Unsupported original polarity"):
        parse_semeval(xml(tmp_path / "bad.xml", polarity="mixed"), "train")
