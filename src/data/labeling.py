"""Proxy xếp hạng cố định và tín hiệu chẩn đoán bất đồng; không có con người nhãn."""

import re

LABEL_TO_ID = {'negative': 0, 'neutral': 1, 'positive': 2}


def rating_label(rating: int) -> str:
    """Xác thực ranh giới nguồn và ánh xạ 1/2, 3, 4/5 một cách nhất quán."""
    if type(rating) is not int or rating not in range(1, 6):
        raise ValueError('Rating must be an integer from 1 to 5')
    return 'negative' if rating <= 2 else 'neutral' if rating == 3 else 'positive'


def noise_reasons(text: str, rating: int) -> list[str]:
    """Gắn cờ các ví dụ ứng cử viên cho con người review sau này; không bao giờ viết lại nhãn đại diện."""
    rating_label(rating)
    normalized = text.casefold().replace('’', "'")
    negative = re.search(r"\b(?:not (?:good|working|worth|happy)|does(?:n't| not) work|"
                         r"won't (?:start|work)|never (?:worked|works)|poor|terrible|"
                         r"disappointing|defective|broken|unusable|returned it)\b", normalized)
    positive = re.search(r"\b(?:works (?:great|perfectly|well)|very happy|highly recommend|"
                         r"excellent|love (?:it|this)|great laptop|good value)\b", normalized)
    # Một tín hiệu đi trước một phủ định rõ ràng không phải là bằng chứng positive.
    if positive and re.search(r"\b(?:not|never|don't|doesn't)\s+(?:\w+\s+){0,2}$",
                              normalized[:positive.start()]):
        positive = None
    reasons = []
    if rating == 5 and negative:
        reasons.append('five_star_negative_or_mixed_cue')
    if rating <= 2 and positive:
        reasons.append('low_star_positive_or_mixed_cue')
    if rating <= 2 and re.search(r'\b(?:average|ordinary|neither good nor bad|just okay)\b', normalized):
        reasons.append('low_star_neutral_cue')
    return reasons
