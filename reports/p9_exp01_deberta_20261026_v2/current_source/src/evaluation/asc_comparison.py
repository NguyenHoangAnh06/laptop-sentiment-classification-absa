"""So sánh predictions theo đúng example ID và cùng gold; không chọn theo test."""
from collections import Counter


def paired_predictions(baseline: list[dict],candidate: list[dict]) -> tuple[dict,list[dict]]:
    """Từ chối lệch thứ tự/gold, đếm bốn nhóm sửa lỗi/hồi quy."""
    if not baseline or [p['example_id'] for p in baseline]!=[p['example_id'] for p in candidate]:
        raise ValueError('Prediction ID/order không khớp')
    counts=Counter({k:0 for k in ['fixed','regressed','both_correct','both_wrong']}); rows=[]
    fields=('text','aspect','start','end','label_id','label','sentence_uid')
    for old,new in zip(baseline,candidate):
        if any(old[k]!=new[k] for k in fields): raise ValueError('Prediction gold/context không khớp')
        a=old['predicted_label_id']==old['label_id']; b=new['predicted_label_id']==new['label_id']
        if old['correct']!=a or new['correct']!=b: raise ValueError('Correct flag không khớp')
        group='both_correct' if a and b else 'both_wrong' if not a and not b else 'fixed' if b else 'regressed'
        counts[group]+=1
        rows.append({**new,'bert_predicted_label_id':old['predicted_label_id'],'comparison_group':group})
    return dict(counts),rows
