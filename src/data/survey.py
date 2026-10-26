"""Proxy chất lượng P1 và lấy mẫu xác định giới hạn tài nguyên, không phải gold nhãn."""

import hashlib
import heapq
import html
import re
import sys
from collections import Counter

from src.data.validation import stable_key

NOT_MEASURED = "NOT_MEASURED"


def normalize_for_survey(text: str) -> str:
    """Giải mã HTML và thu gọn khoảng trắng, giữ nguyên dấu phủ định và dấu câu."""
    text = re.sub(r"</?[A-Za-z][^>]*>", " ", html.unescape(text))
    return " ".join(text.split())


def estimated_size(value) -> int:
    """Ước tính tải trọng Python đệ quy thận trọng; quá trình RSS được đo riêng biệt."""
    size = sys.getsizeof(value)
    if isinstance(value, dict):
        return size + sum(estimated_size(k) + estimated_size(v) for k, v in value.items())
    if isinstance(value, (list, tuple)):
        return size + sum(estimated_size(v) for v in value)
    return size


class BottomSample:
    """Giữ giá trị băm hạt giống thấp nhất với hàng rõ ràng và giới hạn byte ước tính."""

    def __init__(self, capacity: int, seed: int, max_bytes: int = 16_000_000):
        if capacity < 0 or max_bytes <= 0:
            raise ValueError("Invalid sample budget")
        self.capacity, self.seed, self.max_bytes = capacity, seed, max_bytes
        self.heap = []
        self.bytes = 0
        self.budget_rejections = 0
        self.sequence = 0

    def add(self, row: dict) -> None:
        if not self.capacity:
            return
        priority, size = -int(stable_key(row, self.seed), 16), estimated_size(row)
        if len(self.heap) == self.capacity and priority <= self.heap[0][0]:
            return
        removed_size = self.heap[0][3] if len(self.heap) == self.capacity else 0
        if self.bytes + size - removed_size > self.max_bytes:
            self.budget_rejections += 1
            return
        self.sequence += 1
        item = (priority, self.sequence, row, size)
        if len(self.heap) == self.capacity:
            heapq.heapreplace(self.heap, item)
            self.bytes -= removed_size
        else:
            heapq.heappush(self.heap, item)
        self.bytes += size

    def rows(self) -> list[dict]:
        return sorted((item[2] for item in self.heap), key=lambda row: stable_key(row, self.seed))


class ReviewSurvey:
    """Số lượng tập hợp con giới hạn chính xác; vô hiệu hóa rõ ràng số liệu trùng lặp ở giới hạn bộ nhớ."""

    def __init__(self, keywords: list[str], short_words: int, absa_words: int, max_hashes: int):
        self.keywords = keywords
        self.short_words, self.absa_words, self.max_hashes = short_words, absa_words, max_hashes
        self.count = self.words = self.chars = self.short = self.absa_proxy = self.duplicates = 0
        self.ratings, self.products, self.brands, self.length_bins = Counter(), Counter(), Counter(), Counter()
        self.hashes, self.duplicate_complete = set(), True

    def add(self, row: dict) -> None:
        text = normalize_for_survey(row["text"])
        words = len(text.split())
        self.count += 1
        self.words += words
        self.chars += len(text)
        self.short += words < self.short_words
        self.length_bins["0-4" if words < 5 else "5-19" if words < 20 else "20-99" if words < 100 else "100+"] += 1
        self.ratings[str(row["rating"])] += 1
        self.products[row["parent_asin"]] += 1
        if row.get("brand"):
            self.brands[row["brand"]] += 1
        hit = any(re.search(r"\b" + re.escape(word) + r"\b", text, re.I) for word in self.keywords)
        self.absa_proxy += words >= self.absa_words and hit
        digest = hashlib.sha256(text.casefold().encode("utf-8")).digest()
        if self.duplicate_complete:
            if digest in self.hashes:
                self.duplicates += 1
            elif len(self.hashes) < self.max_hashes:
                self.hashes.add(digest)
            else:
                self.duplicate_complete = False
                self.hashes.clear()

    def result(self) -> dict:
        return {
            "valid_reviews": self.count, "unique_products_with_reviews": len(self.products),
            "average_review_length_words": self.words / self.count if self.count else NOT_MEASURED,
            "average_review_length_chars": self.chars / self.count if self.count else NOT_MEASURED,
            "duplicate_percentage": 100 * self.duplicates / self.count if self.count and self.duplicate_complete else NOT_MEASURED,
            "duplicate_definition": "repeat normalized casefolded text, additional occurrences / valid reviews",
            "rating_distribution": {str(r): self.ratings[str(r)] for r in range(1, 6)},
            "language_distribution": NOT_MEASURED,
            "aspect_coverage_estimate": 100 * self.absa_proxy / self.count if self.count else NOT_MEASURED,
            "aspect_method": "keyword hit AND >= min_absa_proxy_words; survey proxy, not ABSA ground truth",
            "short_review_percentage": 100 * self.short / self.count if self.count else NOT_MEASURED,
            "word_length_bins": dict(self.length_bins), "known_brands": len(self.brands),
            "brand_missing_reviews": self.count - sum(self.brands.values()),
            "largest_product_share_percentage": 100 * max(self.products.values()) / self.count if self.count else NOT_MEASURED,
            "proxy_class_distribution": {"negative": self.ratings['1'] + self.ratings['2'], "neutral": self.ratings['3'], "positive": self.ratings['4'] + self.ratings['5']},
            "clean_english_reviews": NOT_MEASURED, "near_duplicate_percentage": NOT_MEASURED,
        }
