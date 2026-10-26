"""Định tuyến ngôn ngữ và tải từng phần của cảm xúc các tệp kết quả tổng thể đã lưu."""

from src.config import load_config


class UnsupportedLanguageError(ValueError):
    """Ngôn ngữ không xác định hoặc dành riêng cho việc triển khai trong tương lai."""


def language_spec(language: str) -> dict:
    """Trả về đặc tả mô hình của ngôn ngữ đã bật mà không cần tải trọng số."""
    spec = load_config("language")["languages"].get(language)
    if spec is None or not spec["enabled"]:
        raise UnsupportedLanguageError(f"Unsupported language: {language}")
    return dict(spec)


def load_sentiment(model_dir, *, family: str, language: str = 'en', root=None, device: str = 'auto'):
    """Tải tổng thể các mô hình được lưu một cách lười biếng, giữ huấn luyện bên ngoài UI/inference."""
    language_spec(language)
    if language != 'en':
        raise UnsupportedLanguageError(f'No implemented model loader for {language}')
    if family == 'bert':
        from src.sentiment.bert import BertArtifact
        return BertArtifact(model_dir, device=device)
    if family == 'classical':
        from src.config import PROJECT_ROOT
        from src.sentiment.classical import load_classical
        return load_classical(model_dir, PROJECT_ROOT if root is None else root)
    raise ValueError(f'Unknown sentiment model family: {family}')
