"""Hợp đồng đầu ra được chia sẻ cho các dự đoán đơn lẻ và lô trong tương lai."""

from dataclasses import asdict, dataclass, field
from math import isfinite

from src.config import load_config
from src.models.registry import language_spec


def _validate_sentiment(sentiment: str, confidence: float | None) -> None:
    if sentiment not in load_config("model")["labels"]:
        raise ValueError(f"Invalid sentiment: {sentiment}")
    if confidence is not None and (
        isinstance(confidence, bool)
        or not isinstance(confidence, (float, int))
        or not isfinite(confidence)
        or not 0 <= confidence <= 1
    ):
        raise ValueError("Confidence must be null or a finite number in [0, 1]")


@dataclass(frozen=True)
class AspectPrediction:
    aspect: str
    sentiment: str
    confidence: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.aspect, str) or not self.aspect.strip():
            raise ValueError("Aspect text must not be empty")
        _validate_sentiment(self.sentiment, self.confidence)


@dataclass(frozen=True)
class ReviewPrediction:
    sentiment: str
    language: str = "en"
    confidence: float | None = None
    aspects: list[AspectPrediction] = field(default_factory=list)
    domain: str = "laptop"

    def __post_init__(self) -> None:
        if self.domain != load_config("data")["domain"]:
            raise ValueError("Only the laptop domain is supported")
        language_spec(self.language)
        _validate_sentiment(self.sentiment, self.confidence)
        if not isinstance(self.aspects, list) or any(
            not isinstance(aspect, AspectPrediction) for aspect in self.aspects
        ):
            raise ValueError("Aspects must be a list of AspectPrediction objects")

    def to_dict(self) -> dict:
        """Tuần tự hóa hợp đồng; điều này không thực hiện mô hình suy luận."""
        return asdict(self)
