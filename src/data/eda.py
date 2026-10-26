"""Mô tả laptop EDA; không có tiền xử lý được trang bị, lựa chọn phân chia hoặc mô hình."""

from collections import Counter
import re

import numpy as np
import pandas as pd

LABELS = ('negative', 'neutral', 'positive')
TOKEN = re.compile(r"[a-z]+(?:'[a-z]+)?")
# Chỉ dành cho bảng tần số mô tả, không bao giờ áp dụng cho văn bản review/model đã lưu.
# Sự phủ định được cố tình giữ lại. Danh sách đầy đủ được ghi lại trong báo cáo bản kê.
STOPWORDS = frozenset('a an the i me my we our you your he she it its they their this that these those and or but if as at by for from in into of on to with is are was were be been being have has had do does did am so very also can will would could should there here then than laptop computer'.split())
# Giả thuyết để điều tra, không trích xuất ABSA vị trí cụm từ hoặc khía cạnh cảm xúc nhãn.
THEMES = {
    'battery': r'\bbatter(?:y|ies)\b',
    'display': r'\b(?:screen|display|resolution|monitor)\b',
    'keyboard': r'\b(?:keyboard|keyboards|keys|touchpad|trackpad)\b',
    'performance': r'\b(?:slow|sluggish|fast|speed|performance|processor|cpu|lag|laggy)\b',
    'build': r'\b(?:hinge|hinges|plastic|chassis|sturdy|flimsy|build quality)\b',
    'price': r'\b(?:price|priced|cost|expensive|cheap|affordable|value)\b',
    'portability': r'\b(?:lightweight|weight|portable|portability|heavy|thin)\b',
    'storage': r'\b(?:ssd|hdd|hard drive|storage|disk)\b',
    'thermals_noise': r'\b(?:overheat\w*|hot|heat|fan|fans|noisy|noise)\b',
}


def wilson_interval(successes: int, total: int) -> tuple[float, float]:
    """Khoảng nhị thức mô tả; Giả định independence/selection không được chứng minh."""
    if total <= 0 or successes < 0 or successes > total:
        raise ValueError('Invalid binomial counts')
    z = 1.959963984540054
    p = successes / total
    denominator = 1 + z*z/total
    center = (p + z*z/(2*total))/denominator
    radius = z * np.sqrt(p*(1-p)/total + z*z/(4*total*total))/denominator
    return (0.0 if successes == 0 else float(center-radius),
            1.0 if successes == total else float(center+radius))


def lexical_tables(frame: pd.DataFrame, min_documents: int = 30) -> dict[str, pd.DataFrame]:
    """Ghi lại tần số và mức độ phổ biến của lớp so với phần còn lại, bảo toàn sự phủ định."""
    counts = {label: Counter() for label in LABELS}
    totals = frame['sentiment'].value_counts().to_dict()
    for text, label in zip(frame['text'], frame['sentiment']):
        tokens = TOKEN.findall(text.lower())
        features = {(1,t) for t in tokens if t not in STOPWORDS}
        for size in (2,3):
            # token gốc liền kề: lọc từ dừng không được tạo ra sự liền kề.
            features.update((size,' '.join(tokens[i:i+size]))
                            for i in range(len(tokens)-size+1)
                            if any(t not in STOPWORDS for t in tokens[i:i+size]))
        counts[label].update(features)
    combined = sum(counts.values(), Counter())
    rows = []
    for (size,term), total in sorted(combined.items()):
        if total < min_documents:
            continue
        for label in LABELS:
            n, k = totals.get(label,0), counts[label][(size,term)]
            other_n, other_k = len(frame)-n, total-k
            rate = k/n if n else 0
            rest_rate = other_k/other_n if other_n else 0
            rows.append(dict(n=size,term=term,sentiment=label,documents=k,
                             class_documents=n,total_documents=total,
                             prevalence=rate,rest_prevalence=rest_rate,
                             prevalence_difference=rate-rest_rate,
                             smoothed_lift=((k+1)/(n+2))/((other_k+1)/(other_n+2))))
    columns = ['n','term','sentiment','documents','class_documents','total_documents',
               'prevalence','rest_prevalence','prevalence_difference','smoothed_lift']
    result = pd.DataFrame(rows,columns=columns)
    frequent = pd.DataFrame([dict(n=size,term=term,documents=count,share=count/len(frame))
                             for (size,term),count in combined.items() if count>=min_documents])
    if not frequent.empty:
        frequent = frequent.sort_values(['n','documents','term'],ascending=[True,False,True]).reset_index(drop=True)
    return {'lexical_by_class': result, 'frequent_terms': frequent}


def group_table(frame: pd.DataFrame, key: str, min_reviews: int) -> pd.DataFrame:
    """Các nhóm đầy đủ có cờ hỗ trợ; không kiểm duyệt hoặc xếp hạng nhóm nhỏ."""
    grouped = frame.groupby(key,dropna=False,sort=True)
    result = grouped.agg(reviews=('rating','size'),products=('parent_asin','nunique'),
                         mean_rating=('rating','mean'),median_words=('word_count','median'),
                         helpful_mean=('helpful_vote','mean'),helpful_median=('helpful_vote','median'),
                         helpful_nonzero_share=('helpful_vote',lambda x: (x>0).mean()),
                         verified_share=('verified_purchase','mean')).reset_index()
    for label in LABELS:
        counts = grouped['sentiment'].apply(lambda x:(x==label).sum()).to_numpy()
        result[label+'_count'] = counts
        result[label+'_share'] = counts/result['reviews']
    bounds = [wilson_interval(int(k),int(n)) for k,n in zip(result['negative_count'],result['reviews'])]
    result['negative_ci_low'] = [x[0] for x in bounds]
    result['negative_ci_high'] = [x[1] for x in bounds]
    result['sufficient_support'] = result['reviews'] >= min_reviews
    return result


def build_tables(frame: pd.DataFrame, min_documents: int = 30) -> tuple[dict, dict[str,pd.DataFrame]]:
    """Tính toán EDA chỉ đọc với mẫu số trên mỗi review rõ ràng."""
    required = {'review_id','text','rating','sentiment','parent_asin','brand_normalized',
                'timestamp','helpful_vote','verified_purchase','clean_text_sha256'}
    if not required <= set(frame):
        raise ValueError(f'Missing fields: {sorted(required-set(frame))}')
    if frame.empty or not set(frame['sentiment']) <= set(LABELS):
        raise ValueError('Empty dataset or invalid proxy labels')
    if frame['text'].isna().any() or not frame['rating'].isin(range(1,6)).all():
        raise ValueError('Invalid text/rating')
    d = frame.copy(deep=True)
    d['character_count'] = d['text'].str.len()
    d['word_count'] = d['text'].str.split().str.len()
    d['lexical_token_count'] = d['text'].map(lambda x:len(TOKEN.findall(x.lower())))
    d['date'] = pd.to_datetime(d['timestamp'],unit='ms',utc=True,errors='coerce')
    d['year'] = d['date'].dt.year.astype('Int64')
    d['month'] = d['date'].dt.strftime('%Y-%m')
    summary = dict(rows=len(d),products=int(d['parent_asin'].nunique()),
                   metadata_brand_categories=int(d['brand_normalized'].nunique()),
                   time_min=str(d['date'].min()),time_max=str(d['date'].max()),
                   invalid_timestamp=int(d['date'].isna().sum()),
                   duplicate_id_excess=int(d['review_id'].duplicated().sum()),
                   duplicate_clean_hash_excess=int(d['clean_text_sha256'].duplicated().sum()),
                   short_under_5_words=int((d['word_count']<5).sum()),
                   helpful_nonzero_share=float((d['helpful_vote']>0).mean()),
                   helpful_median=float(d['helpful_vote'].median()),
                   helpful_max=int(d['helpful_vote'].max()),
                   helpful_words_spearman=float(d[['helpful_vote','word_count']].rank().corr().iloc[0,1]),
                   verified_share=float(d['verified_purchase'].mean()),
                   median_words=float(d['word_count'].median()),
                   p90_words=float(d['word_count'].quantile(.9)))
    tables = {'missing': pd.DataFrame([dict(field=c,missing=int(d[c].isna().sum()),
                                           empty_strings=int(d[c].map(lambda x:isinstance(x,str) and not x.strip()).sum()),
                                           rows=len(d)) for c in frame]),
              'rating': d.groupby('rating').agg(reviews=('review_id','size'),
                    mean_words=('word_count','mean'),median_words=('word_count','median'),
                    mean_helpful=('helpful_vote','mean'),median_helpful=('helpful_vote','median')).reset_index(),
              'sentiment': group_table(d,'sentiment',1),
              'products': group_table(d,'parent_asin',30),
              'brands': group_table(d,'brand_normalized',100),
              'years': group_table(d.dropna(subset=['year']),'year',100),
              'months': group_table(d.dropna(subset=['month']),'month',100),
              'verified': group_table(d,'verified_purchase',30),
              'length_by_sentiment': d.groupby('sentiment')[['character_count','word_count','lexical_token_count']].describe().stack(0,future_stack=True).reset_index(),
              'length_histogram': pd.DataFrame({'bin':['0-4','5-9','10-24','25-49','50-99','100-199','200-499','500-999','1000+'],
                    'reviews':np.histogram(d['word_count'],bins=[0,5,10,25,50,100,200,500,1000,np.inf])[0]})}
    for c in ('rating','sentiment'):
        tables[c]['review_share'] = tables[c]['reviews']/len(d)
    tables.update(lexical_tables(d,min_documents))
    theme_rows, contexts = [], []
    for name,pattern in THEMES.items():
        matched = d['text'].str.contains(pattern,case=False,regex=True)
        for label in LABELS:
            denominator = int((d['sentiment']==label).sum())
            selected = d.loc[matched & (d['sentiment']==label)]
            theme_rows.append(dict(theme=name,sentiment=label,mention_reviews=len(selected),
                                   class_reviews=denominator,
                                   within_class_share=len(selected)/denominator if denominator else 0,
                                   overall_mentions=int(matched.sum()),overall_share=float(matched.mean())))
            for _,row in selected.sort_values('review_id').head(3).iterrows():
                match = re.search(pattern,row['text'],re.I)
                start,end = max(0,match.start()-100),min(len(row['text']),match.end()+160)
                contexts.append(dict(theme=name,proxy_label=label,rating=row['rating'],
                                     review_id=row['review_id'],snippet=row['text'][start:end],
                                     status='LEXICAL_CONTEXT_NOT_ASPECT_SENTIMENT'))
    tables['themes'] = pd.DataFrame(theme_rows)
    tables['theme_contexts'] = pd.DataFrame(contexts)
    product_counts = tables['products']['reviews'].sort_values(ascending=False)
    summary['top_100_products_review_share'] = float(product_counts.head(100).sum()/len(d))
    return summary,tables
