"""Ghép ATE P8 đã khóa với ASC P9; chưa đánh giá Amazon/P10 hoặc overall sentiment."""


class AspectAnalyzer:
    """Nhận extractor/classifier đã tải; chung decoding và occurrence validation với standalone."""
    def __init__(self,extractor,classifier):
        self.extractor=extractor; self.classifier=classifier

    def analyze_aspects(self,text: str,*,language: str='en') -> list[dict]:
        if language!='en': raise ValueError('ABSA hiện chỉ hỗ trợ language=en')
        spans=self.extractor.extract_aspects(text,language=language)
        if not spans: return []
        sentiment=self.classifier.classify_many(text,spans,language=language)
        if len(spans)!=len(sentiment): raise ValueError('ABSA row alignment không khớp')
        return [{'term':a['term'],'start':a['start'],'end':a['end'],'sentiment':s['sentiment'],
                 'aspect_score':None,'sentiment_score':None} for a,s in zip(spans,sentiment)]
