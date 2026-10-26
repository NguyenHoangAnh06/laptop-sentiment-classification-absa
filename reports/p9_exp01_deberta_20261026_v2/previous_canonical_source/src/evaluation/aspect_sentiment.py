"""Chẩn đoán ASC và joint exact span+polarity, tách biệt gold-aspect score."""
from collections import Counter,defaultdict
import re

from src.evaluation.classification import LABELS,classification_metrics


def asc_error_analysis(records: list[dict],train_counts: dict[str,int]) -> dict:
    if any(r['correct']!=(r['label_id']==r['predicted_label_id']) for r in records):
        raise ValueError('ASC correct flag không khớp labels')
    metrics=classification_metrics([r['label_id'] for r in records],[r['predicted_label_id'] for r in records])
    sentence_labels=defaultdict(set); sentence_counts=Counter()
    for row in records:
        sentence_labels[row['sentence_uid']].add(row['label']); sentence_counts[row['sentence_uid']]+=1
    groups=defaultdict(list); examples=[]
    for row in records:
        text=row['text']; uid=row['sentence_uid']
        masks={'all':True,'negation_cue':bool(re.search(r"\b(no|not|never|without)\b|n't",text,re.I)),
               'contrast_cue':bool(re.search(r'\b(but|however|although|yet|whereas)\b',text,re.I)),
               'comparison_cue':bool(re.search(r'\b(better|worse|than)\b',text,re.I)),
               'long_context_gt30_words':len(text.split())>30,
               'multi_aspect_sentence':sentence_counts[uid]>1,'mixed_polarity_sentence':len(sentence_labels[uid])>1,
               'rare_aspect_train_frequency_le1':train_counts.get(row['aspect'].casefold(),0)<=1}
        for group,flag in masks.items():
            if flag: groups[group].append(row)
        if not row['correct']:
            examples.append({**row,'analysis_groups':[k for k,v in masks.items() if v]})
    summary=[]
    for group in ['all','negation_cue','contrast_cue','comparison_cue','long_context_gt30_words',
                  'multi_aspect_sentence','mixed_polarity_sentence','rare_aspect_train_frequency_le1']:
        part=groups[group]; errors=sum(not r['correct'] for r in part)
        summary.append({'group':group,'examples':len(part),'sentences':len({r['sentence_uid'] for r in part}),
                        'errors':errors,'accuracy':(len(part)-errors)/len(part) if part else None})
    return {'metrics':metrics,'groups':summary,'error_examples':examples,
            'semantic_taxonomy':{'implicit_sentiment':'NOT_MEASURED: no opinion-span/human cause tags',
                 'long_distance_sentiment':'NOT_MEASURED: sentence length is only structural proxy',
                 'mixed_same_aspect':'conflict excluded with provenance; not mapped to a three-class target'},
            'note':'Groups overlap; lexical cues are descriptive, not verified causal labels; examples use gold annotations, not new human labels.'}


def joint_metrics(records: list[dict]) -> dict:
    """Exact [start,end)+polarity; conflict gold/pred exact matches bỏ khỏi score, đếm riêng."""
    if not records or len({r['uid'] for r in records})!=len(records): raise ValueError('Joint records/UID không hợp lệ')
    total=Counter(); details=[]
    for row in records:
        gold={}; conflict=set(); pred={}
        for a in row['gold_aspects']:
            span=(a['start'],a['end']); polarity=a['polarity']
            if (not 0<=span[0]<span[1]<=len(row['text']) or row['text'][span[0]:span[1]]!=a['term']
                    or span in gold or span in conflict): raise ValueError('Joint gold span không hợp lệ')
            if polarity=='conflict': conflict.add(span)
            elif polarity in LABELS: gold[span]=polarity
            else: raise ValueError('Joint gold polarity ngoài enum')
        for a in row['predicted_aspects']:
            span=(a['start'],a['end']); label=a['sentiment']
            if (span in pred or not 0<=span[0]<span[1]<=len(row['text']) or label not in LABELS
                    or row['text'][span[0]:span[1]]!=a['term']): raise ValueError('Joint prediction không hợp lệ')
            pred[span]=label
        ignored={p for p in pred if p in conflict}
        filtered={p:l for p,l in pred.items() if p not in ignored}
        exact=set(gold)&set(filtered)
        true={s for s in exact if gold[s]==filtered[s]}
        missing=set(gold)-set(filtered); spurious=set(filtered)-set(gold)
        wrong=exact-true
        pairs=[(g,p) for g in sorted(missing) for p in sorted(spurious) if max(g[0],p[0])<min(g[1],p[1])]
        total.update({'gold_entities':len(gold),'raw_predicted_entities':len(pred),'predicted_entities_scored':len(filtered),
                      'conflict_gold_excluded':len(conflict),'predictions_ignored_exact_conflict':len(ignored),
                      'true_positive':len(true),'false_negative':len(gold)-len(true),'false_positive':len(filtered)-len(true),
                      'extraction_missing_gold_spans':len(missing),'extraction_spurious_predicted_spans':len(spurious),
                      'exact_extraction_matched_spans':len(exact),'sentiment_errors_on_exact_span':len(wrong),
                      'boundary_gold_spans':len({g for g,p in pairs}),'boundary_predicted_spans':len({p for g,p in pairs}),
                      'boundary_pairs':len(pairs),'joint_wrong_span_and_polarity_pairs':sum(gold[g]!=filtered[p] for g,p in pairs),
                      'missed_without_predicted_overlap':sum(not any(max(g[0],p[0])<min(g[1],p[1]) for p in filtered) for g in missing)})
        details.append({'uid':row['uid'],'missing_gold_spans':sorted(missing),'spurious_predicted_spans':sorted(spurious),
                        'sentiment_error_exact_spans':sorted(wrong),'boundary_pairs':pairs,
                        'ignored_conflict_predictions':sorted(ignored)})
    precision=total['true_positive']/total['predicted_entities_scored'] if total['predicted_entities_scored'] else 0.
    recall=total['true_positive']/total['gold_entities'] if total['gold_entities'] else 0.
    return {'precision':precision,'recall':recall,'f1':2*precision*recall/(precision+recall) if precision+recall else 0.,
            'sentences':len(records),'counts':dict(total),'decomposition':details,
            'policy':'exact span+polarity; exclude conflict gold and ignore predictions exactly at conflict spans; partial overlap still counts FP; no partial credit; boundary/joint pairs overlap, not additive causes'}
