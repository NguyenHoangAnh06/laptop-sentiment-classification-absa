"""Bộ đọc mù cho chẩn đoán sentiment; không tạo nhãn người hoặc independent gold."""
from datetime import datetime
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.evaluation.classification import LABELS, classification_metrics
from src.evaluation.error_diagnosis import file_hash
from src.evaluation.sampling_uncertainty import success_total_interval

FIXED=['annotation_id','review_title','review_text']
HUMAN=['human_sentiment','ambiguity','evidence','reviewer_id','reviewed_at']


def ambiguity_flag(value: str) -> bool:
    """Đọc boolean của phiếu hiện hành và enum của phiếu cũ, giữ nguyên dữ liệu."""
    if value in {'TRUE', 'True', 'true', 'mixed', 'insufficient_context'}:
        return True
    if value in {'FALSE', 'False', 'false', 'clear'}:
        return False
    raise ValueError('Ambiguity ngoài enum/boolean')


def fingerprint(row: dict) -> str:
    return hashlib.sha256(json.dumps({k:row[k] for k in FIXED},ensure_ascii=False,sort_keys=True).encode('utf-8')).hexdigest()


def sample_audit(frame: pd.DataFrame, wide: pd.DataFrame, *, seed: int=42,
                 representative_n: int=300, diagnostic_per_class: int=20) -> list[dict]:
    """SRS không hoàn lại và nhóm chọn chủ đích rời nhau; không trộn estimator."""
    if representative_n<1 or representative_n>len(frame) or diagnostic_per_class<0:
        raise ValueError('Kích thước mẫu không hợp lệ')
    if frame.review_id.tolist()!=wide.review_id.tolist():raise ValueError('Audit row alignment FAIL')
    order=np.random.default_rng(seed).choice(len(frame),size=representative_n,replace=False)
    reps=set(int(i) for i in order)
    chosen=[{'row':i,'sampling_group':'representative','inclusion_probability':representative_n/len(frame)} for i in sorted(reps)]
    for label in range(3):
        candidates=[i for i in range(len(frame)) if i not in reps and frame.label_id.iloc[i]==label and wide.competitive_disagreement_count.iloc[i]>0]
        candidates.sort(key=lambda i:(-int(wide.competitive_disagreement_count.iloc[i]),hashlib.sha256(f'{seed}:{frame.review_id.iloc[i]}'.encode()).hexdigest()))
        chosen += [{'row':i,'sampling_group':'diagnostic_enriched','inclusion_probability':None} for i in candidates[:diagnostic_per_class]]
    return chosen


def prepare_audit(frame: pd.DataFrame, wide: pd.DataFrame, kit: Path, inputs: dict, *, seed: int=42,
                  representative_n: int=300, diagnostic_per_class: int=20) -> dict:
    chosen=sample_audit(frame,wide,seed=seed,representative_n=representative_n,diagnostic_per_class=diagnostic_per_class)
    annotations,private=[],[]
    models=[c for c in wide if c.startswith('E0')]
    for sample in chosen:
        i=sample['row'];review=frame.iloc[i]
        aid='D'+hashlib.sha256(f'{seed}:{review.review_id}'.encode()).hexdigest()[:16]
        row={'annotation_id':aid,'review_title':str(review.review_title),'review_text':str(review.text),**{k:'' for k in HUMAN}}
        annotations.append(row)
        private.append({'annotation_id':aid,'review_id':str(review.review_id),'proxy_label_id':int(review.label_id),
                        'rating':float(review.rating),'sampling_group':sample['sampling_group'],
                        'inclusion_probability':sample['inclusion_probability'],'fixed_fingerprint':fingerprint(row),
                        'predictions':{model:int(wide.iloc[i][model]) for model in models}})
    annotations=[annotations[i] for i in np.random.default_rng(seed+1).permutation(len(annotations))]
    if kit.exists():
        manifest=json.loads((kit/'manifest.json').read_text(encoding='utf-8'))
        if manifest['inputs']!=inputs or manifest['seed']!=seed or manifest['representative_n']!=representative_n:
            raise ValueError('Audit kit đã tồn tại nhưng khác input/config; dùng thư mục mới')
        if json.loads((kit/'private_reference.json').read_text(encoding='utf-8'))!=private:
            raise ValueError('Private sidecar thay đổi')
        # Không ghi đè các trường người đã nhập khi chạy lại phân tích.
        read_annotations(kit,require_complete=False)
        return manifest
    kit.mkdir(parents=True,exist_ok=False)
    pd.DataFrame(annotations,columns=FIXED+HUMAN).to_csv(kit/'review_annotation.csv',index=False)
    (kit/'private_reference.json').write_text(json.dumps(private,ensure_ascii=False,indent=2),encoding='utf-8')
    manifest={'status':'PENDING_HUMAN_ANNOTATION','scope':'diagnostic_audit_of_reused_test_not_independent_gold',
              'seed':seed,'population_n':len(frame),'representative_n':representative_n,
              'diagnostic_n':len(private)-representative_n,'row_count':len(private),'inputs':inputs,
              'private_reference_sha256':file_hash(kit/'private_reference.json'),
              'blinded_fields':FIXED+HUMAN,'human_labels_created_by_codex':False}
    (kit/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    return manifest


def read_annotations(kit: Path, *, require_complete: bool=True) -> tuple[pd.DataFrame,list,dict]:
    """Kiểm nhãn/nguồn/người ghi; không biến uncertain thành neutral."""
    manifest=json.loads((kit/'manifest.json').read_text(encoding='utf-8'))
    if file_hash(kit/'private_reference.json')!=manifest['private_reference_sha256']:raise ValueError('Audit sidecar hash FAIL')
    refs=json.loads((kit/'private_reference.json').read_text(encoding='utf-8'))
    if (len(refs)!=manifest['row_count'] or len({r['annotation_id'] for r in refs})!=len(refs)
            or sum(r['sampling_group']=='representative' for r in refs)!=manifest['representative_n']
            or sum(r['sampling_group']=='diagnostic_enriched' for r in refs)!=manifest['diagnostic_n']):
        raise ValueError('Audit manifest/sample counts FAIL')
    frame=pd.read_csv(kit/'review_annotation.csv',keep_default_na=False,dtype=str)
    by_id={r['annotation_id']:r for r in refs}
    if list(frame.columns)!=FIXED+HUMAN or not frame.annotation_id.is_unique or set(frame.annotation_id)!=set(by_id):raise ValueError('Audit IDs/schema FAIL')
    allowed={'',*LABELS,'uncertain'}
    for row in frame.to_dict('records'):
        if fingerprint(row)!=by_id[row['annotation_id']]['fixed_fingerprint']:raise ValueError('Audit text/ID bị sửa')
        if row['human_sentiment'] not in allowed:raise ValueError('Human sentiment ngoài enum')
        if row['ambiguity'] != '':ambiguity_flag(row['ambiguity'])
        if require_complete:
            if not all(row[k].strip() for k in HUMAN):raise ValueError('PENDING: thiếu nhãn/evidence/reviewer/date')
            try:datetime.fromisoformat(row['reviewed_at'].replace('Z','+00:00'))
            except ValueError as exc:raise ValueError('Ngày review phải ISO8601') from exc
    return frame,refs,manifest


def evaluate_audit(kit: Path, *, confirmed_human_review: bool=False) -> dict:
    if not confirmed_human_review:raise ValueError('Cần xác nhận nhãn do con người thực hiện; Codex không tự khai xác nhận')
    frame,refs,manifest=read_annotations(kit)
    annotations=frame.set_index('annotation_id')
    results={'status':'HUMAN_REVIEW_DECLARED_SCHEMA_VALID','human_provenance':'Người vận hành xác nhận; validator không chứng minh độc lập danh tính người gán',
             'scope':manifest['scope'],'imbalance_causal_attribution':'NOT_IDENTIFIABLE_FROM_THIS_AUDIT','groups':{}}
    for group in ['representative','diagnostic_enriched']:
        selected=[r for r in refs if r['sampling_group']==group]
        decided=[r for r in selected if annotations.loc[r['annotation_id'],'human_sentiment'] in LABELS]
        unclear=len(selected)-len(decided)
        mismatch=sum(LABELS[r['proxy_label_id']]!=annotations.loc[r['annotation_id'],'human_sentiment'] for r in decided)
        stats={'audited_n':len(selected),'decisive_n':len(decided),'uncertain_n':unclear,'proxy_human_mismatches':mismatch,
               'mismatch_rate_among_decisive':mismatch/len(decided) if decided else None,'population_estimate_allowed':group=='representative',
               'sample_mismatch_fraction_lower':mismatch/len(selected) if selected else None,
               'sample_mismatch_fraction_upper':(mismatch+unclear)/len(selected) if selected else None,'models':{}}
        if group=='representative' and not unclear:
            lo,hi=success_total_interval(mismatch,len(selected),manifest['population_n'])
            stats['test_population_proxy_mismatch_95pct_interval']=[lo/manifest['population_n'],hi/manifest['population_n']]
        for model in refs[0]['predictions']:
            counts={k:0 for k in ['both_agree','model_error_with_proxy_agreement','proxy_mismatch_model_matches_human','both_disagree_with_human']}
            human=[];pred=[]
            for row in decided:
                h=LABELS.index(annotations.loc[row['annotation_id'],'human_sentiment']);p=row['predictions'][model];proxy=row['proxy_label_id']
                category=('both_agree' if p==h else 'model_error_with_proxy_agreement') if proxy==h else ('proxy_mismatch_model_matches_human' if p==h else 'both_disagree_with_human')
                counts[category]+=1;human.append(h);pred.append(p)
            stats['models'][model]={'diagnostic_counts':counts,'human_metrics_on_decisive_only':classification_metrics(human,pred) if human else None}
        results['groups'][group]=stats
    return results
