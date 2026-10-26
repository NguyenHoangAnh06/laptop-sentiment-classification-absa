"""Kiểm tra hợp đồng P0; tất cả các dự đoán ở đây đều là lịch thi đấu, không phải kết quả mô hình."""

import pytest

from src.config import PROJECT_ROOT, dataset_path, load_config
from src.inference.schema import AspectPrediction, ReviewPrediction
from src.models.registry import UnsupportedLanguageError, language_spec


def test_config_and_paths_are_independent_of_working_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert load_config("data")["domain"] == "laptop"
    assert dataset_path("amazon_raw") == PROJECT_ROOT / "data/raw/amazon"
    model = load_config("model")
    assert model["label_to_id"] == {label: i for i, label in enumerate(model["labels"])}
    assert model["primary_metric"] == "macro_f1"
    assert sum(load_config("data")["split"][key] for key in ("train", "validation", "test")) == 1


def test_language_routing():
    assert language_spec("en")["model_family"] == "BERT"
    assert load_config("language")["languages"]["vi"]["model_family"] == "PhoBERT"
    for language in ("vi", "fr"):
        with pytest.raises(UnsupportedLanguageError):
            ReviewPrediction("positive", language=language)


def test_shared_output_contract():
    prediction = ReviewPrediction("neutral")
    assert prediction.to_dict() == {
        "domain": "laptop", "language": "en", "sentiment": "neutral",
        "confidence": None, "aspects": [],
    }
    aspects = [AspectPrediction("screen", "positive"), AspectPrediction("battery life", "negative")]
    assert len(ReviewPrediction("neutral", aspects=aspects).to_dict()["aspects"]) == 2


@pytest.mark.parametrize("kwargs", [
    {"sentiment": "mixed"}, {"sentiment": "positive", "domain": "phone"},
    {"sentiment": "positive", "confidence": float("nan")},
    {"sentiment": "positive", "confidence": 1.1},
    {"sentiment": "positive", "aspects": ["screen"]},
])
def test_invalid_output_is_rejected(kwargs):
    with pytest.raises(ValueError):
        ReviewPrediction(**kwargs)


def test_empty_aspect_is_rejected():
    with pytest.raises(ValueError):
        AspectPrediction(" ", "neutral")
