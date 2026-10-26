"""Làm sạch tổng thể Amazon-cảm xúc bảo thủ; văn bản gốc vẫn có sẵn."""

import html
import re
from html.parser import HTMLParser


class _ReviewHTML(HTMLParser):
    """Loại bỏ đánh dấu được nhận dạng, giữ lại văn bản, ranh giới từ và các thẻ không xác định."""

    TAGS = {'br', 'p', 'div', 'span', 'b', 'strong', 'i', 'em', 'u', 'a', 'ul', 'ol',
            'li', 'hr', 'blockquote', 'pre', 'code', 'font', 'table', 'tr', 'td',
            'th', 'img', 'html', 'body', 'head', 'h1', 'h2', 'h3', 'h4'}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def handle_starttag(self, tag: str, attrs: list) -> None:
        self.parts.append(' ' if tag in self.TAGS else self.get_starttag_text())

    def handle_endtag(self, tag: str) -> None:
        self.parts.append(' ' if tag in self.TAGS else f'</{tag}>')

    def handle_startendtag(self, tag: str, attrs: list) -> None:
        self.parts.append(' ' if tag in self.TAGS else self.get_starttag_text())


def clean_review(text: str) -> str:
    """Chỉ chuẩn hóa HTML/whitespace; giữ lại URL, trường hợp, dấu câu và phủ định."""
    if not isinstance(text, str):
        raise ValueError('Review text must be a string')
    parser = _ReviewHTML()
    # Trước tiên, hãy giải mã để đánh dấu đã mã hóa được phân tích cú pháp trong lượt này thay vì bị rò rỉ dưới dạng thẻ.
    parser.feed(html.unescape(text))
    parser.close()
    return ' '.join(html.unescape(''.join(parser.parts)).split())


def quality_flags(text: str) -> list[str]:
    """Trả lại các phương pháp phỏng đoán cần thiết của review minh bạch, không bao giờ tự động spam nhãn."""
    tokens = re.findall(r"[\w]+(?:['’][\w]+)?", text.casefold())
    flags = []
    if len(tokens) < 5:
        flags.append('short_under_5_words')
    if re.search(r'https?://|www\.', text, re.I):
        flags.append('url_present_retained')
    if re.search(r'(.)\1{9,}', text):
        flags.append('repeated_character')
    if len(tokens) >= 20 and len(set(tokens)) / len(tokens) < .15:
        flags.append('low_lexical_diversity')
    if re.search(r'(?:buy now|coupon code|click here|visit my|contact me at)', text, re.I):
        flags.append('promotional_phrase')
    if '<script' in text.casefold() or '<style' in text.casefold():
        flags.append('unhandled_script_or_style')
    return flags
