"""Đồ đạc QA tổng hợp, không bao giờ có bằng chứng con người gán nhãn."""

import csv

import pytest

from src.data.filter_qa import validate_product_qa


def qa_file(tmp_path, labels):
    path = tmp_path / "qa.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["group", "parent_asin", "rule_include", "stratum", "human_is_target_product", "human_notes"])
        for i, (rule, label, stratum) in enumerate(labels):
            writer.writerow(["laptop", str(i), rule, stratum, label, "fixture"])
    return path


def test_boolean_labels_stratified_rates_provenance_and_no_mutation(tmp_path):
    path = qa_file(tmp_path, [(True, "True", "included"), (True, "false", "included"),
                              (False, "TRUE", "excluded_near_boundary"),
                              (False, "False", "excluded_other")])
    before = path.read_bytes()
    result = validate_product_qa(path, 2, 0.5, label_provenance="ai_assisted_user_approved")
    assert result["confusion_matrix"] == {"true_positive": 1, "false_positive": 1,
                                          "false_negative": 1, "true_negative": 1}
    assert result["sample_precision"] == 0.5
    assert result["false_positive_fraction_in_included"] == 0.5
    assert result["false_negative_fraction_in_excluded"] == 0.5
    assert result["strata"]["excluded_near_boundary"]["false_negative_fraction_in_excluded"] == 1
    assert result["status"] == "user_approved_sample"
    assert result["independent_human_verified"] is False
    assert result["population_recall"] == result["population_accuracy"] == "NOT_MEASURED"
    assert len(result["misclassified_products"]) == 2
    assert path.read_bytes() == before


@pytest.mark.parametrize("label", ["", "unsure"])
def test_pending_does_not_pass_or_invent_precision(tmp_path, label):
    path = qa_file(tmp_path, [(True, label, "included"), (False, "no", "excluded_other")])
    result = validate_product_qa(path, 1)
    assert result["status"] == "unvalidated"
    assert result["observed_precision"] is None
    assert result["pending_or_unsure"] == 1


@pytest.mark.parametrize("label", ["1", "0", "maybe", "=TRUE()"])
def test_invalid_labels_rejected(tmp_path, label):
    path = qa_file(tmp_path, [(True, label, "included")])
    with pytest.raises(ValueError, match="True/False"):
        validate_product_qa(path, 1)


@pytest.mark.parametrize("bad", ["extra", "missing", "duplicate_id", "duplicate_header"])
def test_malformed_csv_rejected(tmp_path, bad):
    path = qa_file(tmp_path, [(True, "yes", "included")])
    text = path.read_text()
    if bad == "extra":
        text = text.rstrip() + ",extra\n"
    elif bad == "missing":
        text = text.replace(",fixture", "")
    elif bad == "duplicate_id":
        text += text.splitlines()[1] + "\n"
    else:
        text = text.replace("human_notes", "parent_asin")
    path.write_text(text)
    with pytest.raises(ValueError):
        validate_product_qa(path, 1)


def test_unspecified_provenance_never_claims_independent_verification(tmp_path):
    path = qa_file(tmp_path, [(True, "yes", "included")])
    assert validate_product_qa(path, 1)["independent_human_verified"] is False
