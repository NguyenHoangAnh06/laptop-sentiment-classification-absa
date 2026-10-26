"""Hạt giống product/duplicate-component được chia theo các mục tiêu lớp theo tỷ lệ."""

import hashlib
from itertools import combinations

import numpy as np
import pandas as pd

from src.data.labeling import LABEL_TO_ID, rating_label
from src.data.quality_audit import normalize_text
from src.preprocessing.english import classical_text

SPLITS=('train','validation','test')
LABELS=tuple(LABEL_TO_ID)


def content_key(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def split_groups(frame: pd.DataFrame, near_pairs: list[dict]) -> pd.Series:
    """Tham gia các sản phẩm parent/variant và các cạnh trùng lặp; không bao giờ kết nối các đơn vị phân chia."""
    d=frame.reset_index(drop=True)
    if d['review_id'].duplicated().any() or d['parent_asin'].isna().any():
        raise ValueError('Unique IDs and parent products required')
    roots=list(range(len(d)))
    def root(i):
        while roots[i]!=i:
            roots[i]=roots[roots[i]];i=roots[i]
        return i
    def join(a,b):
        a,b=root(a),root(b)
        roots[max(a,b)]=min(a,b)
    columns=['parent_asin','asin','near_duplicate_group_id']
    for column in columns:
        if column not in d:continue
        seen={}
        for i,value in enumerate(d[column]):
            if pd.isna(value) or not value:continue
            if value in seen:join(i,seen[value])
            else:seen[value]=i
    for keys in [d['text'].map(content_key),d['text'].map(lambda x:content_key(normalize_text(x).casefold())),
                 d['text'].map(lambda x:content_key(classical_text(x)))]:
        seen={}
        for i,key in enumerate(keys):
            if key in seen:join(i,seen[key])
            else:seen[key]=i
    by_id={value:i for i,value in enumerate(d['review_id'])}
    for pair in near_pairs:
        a,b=pair['review_id_a'],pair['review_id_b']
        if a in by_id and b in by_id:join(by_id[a],by_id[b])
    members={}
    for i,value in enumerate(d['review_id']):members.setdefault(root(i),[]).append(value)
    names={key:content_key('\n'.join(sorted(values))) for key,values in members.items()}
    return pd.Series([names[root(i)] for i in range(len(d))],index=frame.index,name='split_group_id')


def proportional_targets(class_counts: list[int], ratios: list[float]) -> np.ndarray:
    """Số nguyên class/split hạn ngạch duy trì hàng và lề phân chia theo số dư lớn nhất."""
    if len(ratios)!=3 or any(r<=0 for r in ratios) or not np.isclose(sum(ratios),1):
        raise ValueError('Three positive split ratios must sum to1')
    ideal=np.outer(ratios,class_counts)
    targets=np.floor(ideal).astype(int)
    split_ideal=np.array(ratios)*sum(class_counts)
    row_targets=np.floor(split_ideal).astype(int)
    for i in sorted(range(3),key=lambda i:(-(split_ideal[i]-row_targets[i]),i))[:sum(class_counts)-sum(row_targets)]:
        row_targets[i]+=1
    while targets.sum()<sum(class_counts):
        choices=[(i,j) for i in range(3) for j in range(len(class_counts))
                 if targets[i].sum()<row_targets[i] and targets[:,j].sum()<class_counts[j]]
        i,j=min(choices,key=lambda x:(-(ideal[x]-targets[x]),x))
        targets[i,j]+=1
    return targets


def assign_splits(frame: pd.DataFrame, *, seed: int, ratios: list[float],
                  near_pairs: list[dict] | None = None) -> tuple[pd.DataFrame,dict]:
    """Các thiết bị được kết nối lớn nhất trước tiên; điền vào hạn ngạch lớp còn lại với các đơn vị đơn lẻ."""
    if frame.empty or not set(frame['sentiment'])<=set(LABELS):
        raise ValueError('Empty or invalid proxy labels')
    d=frame.sort_values('review_id').reset_index(drop=True).copy()
    d['split_group_id']=split_groups(d,near_pairs or [])
    class_counts=[int(d['sentiment'].eq(label).sum()) for label in LABELS]
    targets=proportional_targets(class_counts,ratios)
    grouped=pd.crosstab(d['split_group_id'],d['sentiment']).reindex(columns=LABELS,fill_value=0)
    units=[(key,row.to_numpy(dtype=int)) for key,row in grouped.iterrows()]
    def rank(key):return content_key(f'{seed}:{key}')
    units.sort(key=lambda x:(-int(x[1].sum()),rank(x[0])))
    actual=np.zeros_like(targets);assignment={};infeasible=0
    for key,vector in units:
        eligible=[i for i in range(3) if np.all(actual[i]+vector<=targets[i])]
        if not eligible:
            eligible=list(range(3));infeasible+=1
        def objective(i):
            before=actual[i]-targets[i]
            after=actual[i]+vector-targets[i]
            return float(((np.square(after)-np.square(before))/np.maximum(targets[i],1)).sum())
        selected=min(eligible,key=lambda i:(objective(i),rank(f'{key}:{i}')))
        actual[selected]+=vector;assignment[key]=SPLITS[selected]
    d['split']=d['split_group_id'].map(assignment)
    if any(not d['split'].eq(name).any() for name in SPLITS):
        raise ValueError('Grouping leaves an empty split; cannot complete P4')
    return d,{'strategy':'product/variant/normalized/preprocessed/near-duplicate connected groups; deterministic class-balanced greedy',
              'seed':seed,'ratios':dict(zip(SPLITS,ratios)),'target_counts':targets.tolist(),
              'actual_counts':actual.tolist(),'class_order':list(LABELS),'split_order':list(SPLITS),
              'groups':len(units),'max_group_reviews':max(int(v.sum()) for _,v in units),
              'capacity_fallback_groups':infeasible,'exact_class_quotas':bool(np.array_equal(actual,targets))}


def validate_splits(source: pd.DataFrame, assigned: pd.DataFrame, *, qa_ids: set[str],
                    qa_keys: set[bytes], noise: pd.DataFrame, near_pairs: list[dict],
                    excluded_ids: set[str] | None = None) -> dict:
    """Xác thực tư cách thành viên, bình đẳng nguồn và cách ly cross-split/holdout."""
    excluded_ids=excluded_ids or set()
    if assigned.review_id.duplicated().any():raise ValueError('ID assigned more than once')
    if set(assigned.review_id)&excluded_ids or set(assigned.review_id)|excluded_ids!=set(source.review_id):
        raise ValueError('Source row conservation failed')
    expected=source[source.review_id.isin(assigned.review_id)].sort_values('review_id').reset_index(drop=True)
    observed=assigned.sort_values('review_id').reset_index(drop=True)[source.columns]
    pd.testing.assert_frame_equal(expected,observed)
    if not assigned['split'].isin(SPLITS).all():raise ValueError('Invalid split name')
    required=['review_id','parent_asin','text','raw_text','sentiment','label_id','clean_text_sha256']
    for column in required:
        if assigned[column].isna().any() or assigned[column].map(lambda v:isinstance(v,str) and not v.strip()).any():
            raise ValueError(f'Invalid/missing {column}')
    if not all(assigned.label_id==assigned.sentiment.map(LABEL_TO_ID)):
        raise ValueError('Invalid label IDs')
    if not assigned['rating'].isin(range(1,6)).all() or not assigned['sentiment'].eq(assigned['rating'].map(rating_label)).all():
        raise ValueError('Invalid rating-derived proxy mapping')
    if not assigned['language'].eq('en').all() or not assigned['label_provenance'].eq('rating-derived proxy').all():
        raise ValueError('Invalid language/provenance')
    ids_by_split={name:set(assigned.loc[assigned.split.eq(name),'review_id']) for name in SPLITS}
    checks={}
    for column in ['review_id','parent_asin','asin','split_group_id','text','clean_text_sha256']:
        if column not in assigned:continue
        sets={name:set(assigned.loc[assigned.split.eq(name),column].dropna()) for name in SPLITS}
        checks[column]={f'{a}__{b}':len(sets[a]&sets[b]) for a,b in combinations(SPLITS,2)}
    for name,transform in [('normalized_text',lambda t:normalize_text(t).casefold()),('classical_text',classical_text)]:
        sets={split:{content_key(transform(t)) for t in assigned.loc[assigned.split.eq(split),'text']} for split in SPLITS}
        checks[name]={f'{a}__{b}':len(sets[a]&sets[b]) for a,b in combinations(SPLITS,2)}
    if any(value for group in checks.values() for value in group.values()):raise ValueError('Cross-split leakage')
    split_by_id=dict(zip(assigned.review_id,assigned.split))
    near_cross=sum(a in split_by_id and b in split_by_id and split_by_id[a]!=split_by_id[b]
                   for p in near_pairs for a,b in [(p['review_id_a'],p['review_id_b'])])
    holdout_near=sum((p['review_id_a'] in split_by_id)!=(p['review_id_b'] in split_by_id)
                     for p in near_pairs)
    if near_cross or holdout_near:raise ValueError('Near-duplicate split/holdout leakage')
    qa_id=len(set(assigned.review_id)&qa_ids)
    qa_text=sum(bytes.fromhex(h) in qa_keys for h in assigned.clean_text_sha256)
    noise_id=len(set(assigned.review_id)&set(noise.review_id))
    noise_text=len(set(assigned.clean_text_sha256)&set(noise.clean_text_sha256))
    if qa_id or qa_text or noise_id or noise_text:raise ValueError('QA/noise contamination')
    counts={name:{'rows':len(ids_by_split[name]),'products':int(assigned.loc[assigned.split.eq(name),'parent_asin'].nunique()),
                  'labels':{label:int((assigned.split.eq(name)&assigned.sentiment.eq(label)).sum()) for label in LABELS}}
            for name in SPLITS}
    if any(not k for values in counts.values() for k in values['labels'].values()):
        raise ValueError('All3classes required in each split')
    users={name:set(assigned.loc[assigned.split.eq(name),'user_id'].dropna()) for name in SPLITS}
    return {'status':'PASS','source_rows':len(source),'assigned_rows':len(assigned),'excluded_rows':len(excluded_ids),
            'cross_split_overlaps':checks,'near_cross_split_pairs':near_cross,'near_holdout_pairs':holdout_near,
            'qa_id_overlap':qa_id,'qa_text_overlap':qa_text,'diagnostic_id_overlap':noise_id,
            'diagnostic_text_overlap':noise_text,'counts':counts,
            'user_overlap_diagnostic':{f'{a}__{b}':len(users[a]&users[b]) for a,b in combinations(SPLITS,2)},
            'user_isolation_required':False,'features':['text'],'rating_metadata_features':False,
            'p10_gold_status':'NOT_CREATED; future independent gold must exclude training IDs/text groups'}
