"""Chọn lát cắt EDA mô tả từ bảng cũ, không đọc hoặc biến đổi review."""

import re

import pandas as pd

from src.data.eda import LABELS


def phrase_rates(frame: pd.DataFrame) -> pd.DataFrame:
    """Tính lại tỷ lệ trong/ngoài lớp từ số bài, tránh dùng số đã làm tròn."""
    required = {'n', 'term', 'sentiment', 'documents', 'class_documents', 'total_documents'}
    if not required <= set(frame):
        raise ValueError('Thiếu trường số đếm trong bảng phrase')
    result = frame.copy(deep=True)
    if not set(result.sentiment) <= set(LABELS):
        raise ValueError('Nhãn phrase không hợp lệ')
    if result.duplicated(['n', 'term', 'sentiment']).any():
        raise ValueError('Phrase/lớp bị trùng')
    for _, group in result.groupby(['n', 'term'], sort=False):
        if set(group.sentiment) != set(LABELS) or group.total_documents.nunique() != 1:
            raise ValueError('Thiếu lớp hoặc tổng document không nhất quán')
        if group.documents.sum() != group.total_documents.iloc[0]:
            raise ValueError('Tổng số bài chứa phrase không khớp các lớp')
    total_rows = result.groupby('sentiment').class_documents.agg(['min', 'max'])
    if (total_rows['min'] != total_rows['max']).any():
        raise ValueError('Mẫu số lớp thay đổi giữa các phrase')
    total = total_rows['max'].sum()
    rest_n = total - result.class_documents
    rest_k = result.total_documents - result.documents
    invalid = ((result.class_documents <= 0) | (rest_n <= 0) |
               (result.documents < 0) | (result.documents > result.class_documents) |
               (rest_k < 0) | (rest_k > rest_n))
    if invalid.any():
        raise ValueError('Số đếm hoặc mẫu số phrase không hợp lệ')
    result['outside_documents'] = rest_k
    result['outside_class_documents'] = rest_n
    result['prevalence'] = result.documents / result.class_documents
    result['rest_prevalence'] = rest_k / rest_n
    result['prevalence_difference'] = result.prevalence - result.rest_prevalence
    result['smoothed_lift'] = ((result.documents + 1) / (result.class_documents + 2)) / ((rest_k + 1) / (rest_n + 2))
    return result


def select_phrases(frame: pd.DataFrame, minimum: int = 30, top: int = 5,
                   n: int | None = 2, pattern: str | None = None,
                   labels: tuple[str, ...] = LABELS) -> pd.DataFrame:
    """Xếp hạng effect size rồi support/từ điển, không hard-code phrase thắng."""
    if minimum < 1 or top < 1:
        raise ValueError('Support và top phải dương')
    rates = phrase_rates(frame)
    selected = rates[(rates.documents >= minimum) & (rates.prevalence_difference > 0)]
    if n is not None:
        selected = selected[selected.n == n]
    else:
        selected = selected[selected.n.isin([2, 3])]
    if pattern is not None:
        re.compile(pattern)
        selected = selected[selected.term.str.contains(pattern, regex=True)]
    ordered = []
    for label in labels:
        rows = selected[selected.sentiment == label].sort_values(
            ['prevalence_difference', 'documents', 'term'], ascending=[False, False, True])
        ordered.append(rows.head(top))
    return pd.concat(ordered, ignore_index=True)


def compact_tables(tables: dict[str, pd.DataFrame], cfg: dict) -> dict[str, pd.DataFrame]:
    """Giữ tám bảng core, trong đó traceability được bổ sung ở lớp báo cáo."""
    snapshot = tables['sentiment'][['sentiment', 'reviews', 'review_share']].copy()
    if set(snapshot.sentiment) != set(LABELS) or snapshot.reviews.sum() <= 0:
        raise ValueError('Snapshot nhãn không hợp lệ')
    if ((snapshot.review_share - snapshot.reviews / snapshot.reviews.sum()).abs() > 1e-9).any():
        raise ValueError('Tỷ lệ nhãn không khớp mẫu số')
    length = tables['length_by_sentiment'].query("level_1 == 'word_count'")[
        ['sentiment', 'count', '25%', '50%', '75%']].copy()
    length.columns = ['sentiment', 'reviews', 'q25_words', 'median_words', 'q75_words']
    length['iqr_words'] = length.q75_words - length.q25_words
    for r in length.itertuples():
        expected = snapshot.loc[snapshot.sentiment == r.sentiment, 'reviews']
        if len(expected) != 1 or r.reviews != expected.iloc[0]:
            raise ValueError('Mẫu số độ dài khác snapshot')
        if not r.q25_words <= r.median_words <= r.q75_words:
            raise ValueError('Phân vị độ dài không tăng')
    lexical = cfg['lexical']
    distinctive = select_phrases(tables['lexical_by_class'], lexical['minimum_class_documents'],
                                 lexical['top_per_class'], lexical['phrase_length'])
    failure = select_phrases(tables['lexical_by_class'], lexical['minimum_class_documents'],
                             lexical['failure_top'], None, lexical['failure_pattern'], ('negative',))
    themes = tables['themes'].pivot(index='theme', columns='sentiment', values='mention_reviews')
    themes = themes.reindex(columns=LABELS).reset_index()
    for label in LABELS:
        n = int(snapshot.set_index('sentiment').loc[label, 'reviews'])
        themes[label + '_rate'] = themes[label] / n
    products = tables['products'].sort_values(['reviews', 'parent_asin'], ascending=[False, True])
    brands = tables['brands'].sort_values(['reviews', 'brand_normalized'], ascending=[False, True])
    total = int(snapshot.reviews.sum())
    concentration = pd.DataFrame([
        {'scope': 'product', 'indicator': 'products_total', 'numerator': len(products), 'denominator': len(products)},
        {'scope': 'product', 'indicator': 'singleton_products', 'numerator': int((products.reviews == 1).sum()), 'denominator': len(products)},
        {'scope': 'product', 'indicator': 'top100_review_share', 'numerator': int(products.head(100).reviews.sum()), 'denominator': total},
        {'scope': 'product', 'indicator': 'maximum_reviews_per_product', 'numerator': int(products.reviews.max()), 'denominator': None},
        {'scope': 'brand', 'indicator': 'top5_review_share', 'numerator': int(brands.head(5).reviews.sum()), 'denominator': total},
    ])
    concentration['share'] = concentration.numerator / concentration.denominator
    verified = tables['verified'][['verified_purchase', 'reviews', 'negative_count', 'neutral_count',
                                    'negative_share', 'neutral_share', 'median_words']].copy()
    return {'snapshot': snapshot, 'length': length, 'phrases': distinctive,
            'failure_phrases': failure, 'theme_rates': themes,
            'concentration': concentration, 'verified': verified}
