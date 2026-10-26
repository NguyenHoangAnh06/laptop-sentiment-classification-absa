"""Chẩn đoán từ saved predictions: mô tả bất đồng proxy, không tự quy nguyên nhân."""
import hashlib
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

from src.evaluation.classification import LABELS, classification_metrics
from src.preprocessing.semantic import canonical_text


def file_hash(path: Path) -> str:
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def redact_excerpt(text: str) -> str:
    """Ẩn mẫu liên hệ phổ biến; không phải audit PII bằng người."""
    text=re.sub(r'https?://\S+|\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b','[ẩn liên hệ]',text)
    text=re.sub(r'(?<!\w)\+?\d[\d ()-]{7,}\d(?!\w)','[ẩn số]',text)
    text=re.sub(r'(?i)\bmy name is\s+\w+(?:\s+\w+)?','[ẩn tên]',text)
    return text[:220]


def load_predictions(root: Path, frame: pd.DataFrame, completion: dict) -> tuple[dict,dict]:
    """Dùng provenance active, đối chiếu ID/nhãn/metric; không tải estimator."""
    predictions,provenance={},{}
    table=pd.read_csv(root/'reports/p7_unified_results.csv').set_index('model')
    for name in completion['models']:
        cloud=completion.get('model_sources',{}).get(name)
        if cloud:
            folder=root/cloud['directory'];path=folder/'test_predictions.csv'
            p=pd.read_csv(path,dtype={'review_id':str})
            truth,pred=p.y_true.to_numpy(),p.y_pred.to_numpy()
        else:
            folder=root/'reports/semantic_20261024'/name
            if (folder/'latest_attempt.json').exists():
                folder=folder/'attempts'/json.loads((folder/'latest_attempt.json').read_text(encoding='utf-8'))['attempt']
            path=folder/'test_predictions.parquet';p=pd.read_parquet(path)
            truth,pred=p.label_id.to_numpy(),p.prediction_id.to_numpy()
        if frame.review_id.tolist()!=p.review_id.tolist() or not np.array_equal(frame.label_id,truth):
            raise ValueError('Prediction ID/order/y_true không khớp: '+name)
        if pred.dtype.kind not in 'iu' or not np.isin(pred,[0,1,2]).all():raise ValueError('Nhãn dự đoán không hợp lệ')
        metrics=classification_metrics(truth,pred)
        if not np.isclose(metrics['macro_f1'],table.loc[name,'macro_f1'],atol=1e-12,rtol=0):raise ValueError('Metric không khớp bảng active')
        predictions[name]=pred
        provenance[name]={'path':path.relative_to(root).as_posix(),'sha256':file_hash(path),
                          'train_samples':int(table.loc[name,'train_samples']),'regime':str(table.loc[name,'data_regime'])}
    return predictions,provenance


def error_tables(frame: pd.DataFrame, predictions: dict) -> dict[str,pd.DataFrame]:
    """Mẫu số là support của từng nhóm; nhóm lexical có thể chồng lấn."""
    texts=canonical_text(frame);truth=frame.label_id.to_numpy()
    lengths=np.array([len(t.split()) for t in texts])
    masks={'all':np.ones(len(frame),dtype=bool),'short_10_words':lengths<=10,
           'long_200_words':lengths>200,
           'negation_cue':np.array([bool(re.search(r"\b(no|not|never|without)\b|n't",t,re.I)) for t in texts]),
           'mixed_cues_heuristic':np.array([bool(re.search(r'\b(good|great|excellent|love)\b',t,re.I)) and bool(re.search(r'\b(bad|poor|broken|slow|hate)\b',t,re.I)) for t in texts]),
           'proxy_neutral':truth==1}
    groups,transitions,classes,ratings,examples=[],[],[],[],[]
    wide=frame[['review_id','rating','label_id']].copy()
    for name,pred in predictions.items():
        wide[name]=pred;errors=truth!=pred
        metrics=classification_metrics(truth,pred)
        for a,label in enumerate(LABELS):
            mask=truth==a;support=int(mask.sum());pred_count=int((pred==a).sum())
            classes.append({'model':name,'class':label,'support':support,'true_share':support/len(frame),
                            'predicted_count':pred_count,'predicted_share':pred_count/len(frame),
                            'proxy_disagreements':int((mask&errors).sum()),'error_rate_within_class':float(errors[mask].mean()) if support else None,
                            **metrics['per_class'][label]})
            for b in range(3):
                count=int(((truth==a)&(pred==b)).sum())
                transitions.append({'model':name,'proxy_label_id':a,'prediction_id':b,'count':count,
                                    'source_class_support':support,'rate_within_source_class':count/support if support else None})
        for category,mask in masks.items():
            support=int(mask.sum());count=int((mask&errors).sum())
            groups.append({'model':name,'category':category,'support':support,'errors':count,'proxy_disagreement_rate':count/support if support else None})
            if category=='all':continue
            # Duyệt theo ID ổn định, không gọi các ví dụ này là nhãn người.
            indices=sorted(np.flatnonzero(mask&errors),key=lambda i:str(frame.review_id.iloc[i]))[:3]
            for i in indices:
                examples.append({'review_id':frame.review_id.iloc[i],'model':name,'text_excerpt':redact_excerpt(texts[i]),
                    'proxy_label':LABELS[truth[i]],'prediction':LABELS[pred[i]],'confidence':None,'error_category':category,
                    'human_verified':False,'star_text_mismatch':'PENDING: cần người xác minh; không suy từ bất đồng model/proxy'})
        for rating in sorted(frame.rating.unique()):
            mask=frame.rating.to_numpy()==rating
            ratings.append({'model':name,'rating':rating,'support':int(mask.sum()),'errors':int((mask&errors).sum()),
                            'proxy_disagreement_rate':float(errors[mask].mean())})
    competitive=[name for name in predictions if name!='E00_majority']
    matrix=np.stack([predictions[n] for n in competitive],axis=1)
    wrong=(matrix!=truth[:,None]).sum(axis=1)
    wide['competitive_disagreement_count']=wrong
    wide['competitive_distinct_predictions']=[len(set(row)) for row in matrix]
    agreement=[]
    for k in range(len(competitive)+1):
        for a,label in enumerate(LABELS):
            agreement.append({'proxy_class':label,'competitive_models_disagreeing_with_proxy':k,
                              'support':int(((wrong==k)&(truth==a)).sum()),'human_cause_status':'NOT_MEASURED'})
    return {'groups':pd.DataFrame(groups),'transitions':pd.DataFrame(transitions),'classes':pd.DataFrame(classes),
            'ratings':pd.DataFrame(ratings),'examples':pd.DataFrame(examples),'review_predictions':wide,
            'agreement':pd.DataFrame(agreement)}


def imbalance_evidence(frames: dict, history: list) -> tuple[pd.DataFrame,pd.DataFrame]:
    """Tóm tắt thực nghiệm validation đã có; không chạy lại balanced test."""
    distribution=[]
    train_counts=np.bincount(frames['train'].label_id,minlength=3)
    for split,frame in frames.items():
        for i,label in enumerate(LABELS):
            n=int((frame.label_id==i).sum())
            distribution.append({'split':split,'class':label,'count':n,'share':n/len(frame),
                                 'inverse_frequency_weight_train':len(frames['train'])/(3*train_counts[i])})
    selected={mode:max((r for r in history if r['mode']==mode),key=lambda r:r['validation']['macro_f1'])['epoch'] for mode in ['unweighted','balanced']}
    rows=[]
    for row in history:
        m=row['validation'];neutral=m['per_class']['neutral']
        rows.append({'mode':row['mode'],'epoch':row['epoch'],'validation_macro_f1':m['macro_f1'],
                     'neutral_precision':neutral['precision'],'neutral_recall':neutral['recall'],'neutral_f1':neutral['f1'],
                     'negative_f1':m['per_class']['negative']['f1'],'positive_f1':m['per_class']['positive']['f1'],
                     'selected_within_mode_by_validation_macro_f1':row['epoch']==selected[row['mode']]})
    return pd.DataFrame(distribution),pd.DataFrame(rows)


def weighting_pairs(truth, unweighted, balanced) -> pd.DataFrame:
    """Đếm sửa được/làm sai thêm trên cùng validation; không diễn giải là causal fraction."""
    truth,unweighted,balanced=map(np.asarray,(truth,unweighted,balanced))
    classification_metrics(truth,unweighted)
    classification_metrics(truth,balanced)
    old_ok=unweighted==truth;new_ok=balanced==truth
    rows=[]
    for i,label in enumerate(LABELS):
        mask=truth==i
        rows.append({'class':label,'support':int(mask.sum()),
                     'both_correct':int((mask&old_ok&new_ok).sum()),
                     'corrected_by_balanced':int((mask&~old_ok&new_ok).sum()),
                     'regressed_by_balanced':int((mask&old_ok&~new_ok).sum()),
                     'both_wrong':int((mask&~old_ok&~new_ok).sum()),
                     'unweighted_false_positives':int(((unweighted==i)&~mask).sum()),
                     'balanced_false_positives':int(((balanced==i)&~mask).sum())})
    return pd.DataFrame(rows)
