"""Metric strict character-span và phân tích lỗi ATE, không dùng polarity."""
from collections import Counter


def span_set(aspects: list[dict]) -> set[tuple[int, int]]:
    """Span bán mở [start,end); term không thay thế character offsets."""
    spans = [(a['start'], a['end']) for a in aspects]
    if any(type(a) is not int or type(b) is not int or a < 0 or b <= a for a,b in spans):
        raise ValueError('Span không hợp lệ')
    if len(spans) != len(set(spans)):
        raise ValueError('Duplicate aspect span')
    return set(spans)


def entity_metrics(records: list[dict]) -> dict:
    """Micro P/R/F1 theo entity chính xác toàn ranh giới, kể cả câu không aspect."""
    if not records or len({r['uid'] for r in records}) != len(records):
        raise ValueError('Cần predictions không rỗng, UID duy nhất')
    tp = gold_n = pred_n = 0
    for row in records:
        gold, pred = span_set(row['gold_aspects']), span_set(row['predicted_aspects'])
        if any(b > len(row['text']) for a,b in gold | pred):
            raise ValueError('Span vượt sentence')
        for key in ['gold_aspects', 'predicted_aspects']:
            if any(a['term'] != row['text'][a['start']:a['end']] for a in row[key]):
                raise ValueError('Term/span không khớp text')
        tp += len(gold & pred); gold_n += len(gold); pred_n += len(pred)
    precision = tp/pred_n if pred_n else 0.
    recall = tp/gold_n if gold_n else 0.
    return {'entity_precision': precision, 'entity_recall': recall,
            'entity_f1': 2*precision*recall/(precision+recall) if precision+recall else 0.,
            'true_positive': tp, 'false_positive': pred_n-tp, 'false_negative': gold_n-tp,
            'gold_entities': gold_n, 'predicted_entities': pred_n, 'sentences': len(records),
            'convention': 'micro_exact_character_span_no_partial_credit'}


def error_analysis(records: list[dict], train_term_counts: dict[str,int]) -> dict:
    """Taxonomy có mẫu số rõ; nhóm phụ chồng lấn, không gán nguyên nhân bằng suy đoán."""
    metrics = entity_metrics(records)
    counts = Counter()
    examples = []
    for row in records:
        gold = {tuple((a['start'],a['end'])):a for a in row['gold_aspects']}
        pred = {tuple((a['start'],a['end'])):a for a in row['predicted_aspects']}
        missed, spurious = set(gold)-set(pred), set(pred)-set(gold)
        # Boundary pairs là quan hệ nhiều-nhiều; không trừ chúng khỏi FP/FN.
        pairs = [(g,p) for g in sorted(missed) for p in sorted(spurious)
                 if max(g[0],p[0]) < min(g[1],p[1])]
        counts['boundary_pairs'] += len(pairs)
        counts['boundary_gold_entities'] += len({g for g,p in pairs})
        counts['boundary_predicted_entities'] += len({p for g,p in pairs})
        counts['missed_without_overlap'] += sum(not any(max(g[0],p[0]) < min(g[1],p[1]) for p in pred) for g in missed)
        counts['false_positive_without_overlap'] += sum(not any(max(g[0],p[0]) < min(g[1],p[1]) for g in gold) for p in spurious)
        for g, aspect in gold.items():
            term = aspect['term'].casefold()
            multi = len(aspect['term'].split()) > 1
            rare = train_term_counts.get(term,0) <= 1
            counts['multiword_gold'] += multi
            counts['multiword_missed'] += multi and g in missed
            counts['rare_gold'] += rare
            counts['rare_missed'] += rare and g in missed
            # Proxy nhóm cấu trúc, không tự khẳng định đó là compound kỹ thuật.
            long_phrase = len(aspect['term'].split()) >= 3
            counts['long_phrase_gold'] += long_phrase
            counts['long_phrase_missed'] += long_phrase and g in missed
            generic = term in {'system','machine','thing'}
            counts['generic_gold'] += generic
            counts['generic_missed'] += generic and g in missed
        if len(gold) > 1:
            counts['multiple_aspect_sentences'] += 1
            counts['multiple_aspect_sentences_with_error'] += bool(missed or spurious)
        if missed or spurious:
            counts['sentences_with_error'] += 1
            examples.append({'uid': row['uid'], 'sentence_id': row['sentence_id'],
                             'gold_aspects': row['gold_aspects'], 'predicted_aspects': row['predicted_aspects'],
                             'missed_spans': sorted(missed), 'false_positive_spans': sorted(spurious),
                             'boundary_pairs': pairs})
    keys = ['boundary_pairs','boundary_gold_entities','boundary_predicted_entities','missed_without_overlap',
            'false_positive_without_overlap','multiword_gold','multiword_missed','rare_gold','rare_missed',
            'long_phrase_gold','long_phrase_missed','generic_gold','generic_missed',
            'multiple_aspect_sentences','multiple_aspect_sentences_with_error','sentences_with_error']
    return {'metrics': metrics, 'counts': {k:int(counts[k]) for k in keys},
            'policy': 'FP/FN exact; boundary pairs overlap; rare=train frequency<=1; multiword=whitespace words>1; long_phrase>=3 words is structural proxy, not human technical taxonomy',
            'examples': examples}
