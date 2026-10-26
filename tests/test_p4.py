"""Đồ đạc splitting/preprocessing tổng hợp; không có gán nhãn hoặc mô hình huấn luyện thực sự."""

import joblib
import numpy as np
import pandas as pd
import pytest
from tokenizers import Tokenizer, models, normalizers, pre_tokenizers, processors

from scripts.prepare_p4 import reserve_holdout_matches
from src.data.split import LABELS, SPLITS, assign_splits, content_key, proportional_targets, split_groups, validate_splits
from src.preprocessing.english import ClassicalPreprocessor, classical_text, minimal_text, ordered_id_digest
from src.preprocessing.bert import BertPreprocessor, choose_max_length


@pytest.fixture
def source():
    rows=[]
    for product in range(20):
        for label_id,(label,rating) in enumerate(zip(LABELS,[1,3,5])):
            i=product*3+label_id
            text=f'Product {product} review {i}: not never no, works!'
            rows.append(dict(review_id=f'fixture:{i:03}',parent_asin=f'p{product}',asin=f'a{product}',
                text=text,raw_text=text,rating=rating,sentiment=label,label_id=label_id,
                label_provenance='rating-derived proxy',language='en',user_id=f'u{i//5}',
                clean_text_sha256=content_key(text.casefold()),near_duplicate_group_id=None))
    return pd.DataFrame(rows)


def test_exact_proportions_group_isolation_and_replay(source):
    assigned,info=assign_splits(source,seed=42,ratios=[.7,.15,.15])
    replay,again=assign_splits(source.sample(frac=1,random_state=7),seed=42,ratios=[.7,.15,.15])
    pd.testing.assert_frame_equal(assigned,replay)
    assert info==again and info['exact_class_quotas']
    assert assigned.groupby('parent_asin')['split'].nunique().max()==1
    result=validate_splits(source,assigned,qa_ids=set(),qa_keys=set(),
        noise=pd.DataFrame(columns=['review_id','clean_text_sha256']),near_pairs=[])
    assert [result['counts'][s]['rows'] for s in SPLITS]==[42,9,9]
    assert all(result['counts'][s]['labels']==dict.fromkeys(LABELS,n) for s,n in zip(SPLITS,[14,3,3]))


def test_variant_normalized_and_near_connected_components(source):
    source.loc[3,'asin']=source.loc[0,'asin']  # biến thể bí danh cầu nối cha mẹ
    source.loc[6,'text']=source.loc[0,'text'].upper()
    pairs=[{'review_id_a':source.loc[0,'review_id'],'review_id_b':source.loc[9,'review_id']}]
    groups=split_groups(source,pairs)
    assert len({groups[i] for i in [0,3,6,9]})==1
    assert groups[1]==groups[0] and groups[4]==groups[0]


def test_unbalanced_indivisible_groups_report_deviation():
    d=pd.DataFrame([dict(review_id=f'r{i}',parent_asin=f'p{i//9}',asin=f'p{i//9}',
                         text=f'unique text{i}',sentiment=LABELS[i%3]) for i in range(90)])
    _,info=assign_splits(d,seed=42,ratios=[.7,.15,.15])
    assert not info['exact_class_quotas'] and info['capacity_fallback_groups']>0
    assert sum(sum(x) for x in info['actual_counts'])==90


def test_impossible_nonempty_group_split_fails():
    d=pd.DataFrame([dict(review_id=f'r{i}',parent_asin='only-one-product',
                         text=f'unique text{i}',sentiment=LABELS[i%3]) for i in range(9)])
    with pytest.raises(ValueError,match='empty split'):
        assign_splits(d,seed=42,ratios=[.7,.15,.15])


def test_validator_rejects_cross_product_holdout_and_foreign_rows(source):
    assigned,_=assign_splits(source,seed=42,ratios=[.7,.15,.15])
    kwargs=dict(qa_ids=set(),qa_keys=set(),noise=pd.DataFrame(columns=['review_id','clean_text_sha256']),near_pairs=[])
    bad=assigned.copy();bad.loc[0,'split']='test' if bad.loc[0,'split']!='test' else 'train'
    with pytest.raises(ValueError,match='leakage'):validate_splits(source,bad,**kwargs)
    with pytest.raises(ValueError,match='contamination'):
        validate_splits(source,assigned,**{**kwargs,'qa_ids':{assigned.loc[0,'review_id']}})
    foreign=assigned.copy();foreign.loc[0,'review_id']='foreign'
    with pytest.raises(ValueError,match='conservation'):validate_splits(source,foreign,**kwargs)
    changed=assigned.copy();changed.loc[0,'raw_text']='silently modified'
    with pytest.raises(AssertionError):validate_splits(source,changed,**kwargs)


def test_holdout_reservation_preserves_source_and_propagates_near(source):
    holds=[{'review_id':'holdout:1','text':source.loc[0,'text'],'sentiment':'holdout'}]
    pairs=[dict(review_id_a='holdout:1',review_id_b=source.loc[3,'review_id']),
           dict(review_id_a=source.loc[3,'review_id'],review_id_b=source.loc[6,'review_id'])]
    original=source.copy(deep=True)
    excluded=reserve_holdout_matches(source,holds,set(),pairs)
    assert set(excluded)==set(source.loc[[0,3,6],'review_id'])
    assert excluded[source.loc[6,'review_id']]=='holdout_near_cluster'
    pd.testing.assert_frame_equal(source,original)


def test_integer_quota_margins():
    target=proportional_targets([8259,2631,19110],[.7,.15,.15])
    assert target.sum(axis=1).tolist()==[21000,4500,4500]
    assert target.sum(axis=0).tolist()==[8259,2631,19110]
    with pytest.raises(ValueError):proportional_targets([10,10,10],[.8,.15,.15])


def test_tfidf_train_only_no_target_features_and_frozen_oov(tmp_path):
    train=pd.DataFrame(dict(review_id=['a','b'],split=['train','train'],
                            text=["not never no don't bad!",'good great!'],rating=[1,5],sentiment=['negative','positive']))
    pipeline=ClassicalPreprocessor(min_df=1,max_features=100)
    matrix=pipeline.fit_train(train)
    assert matrix.shape[0]==2
    words=pipeline.vectorizer.vocabulary_
    assert all(t in words for t in ['not','never','no',"don't",'!'])
    assert 'rating' not in words and 'negative' not in words
    before=pipeline.vectorizer.idf_.copy()
    held=pd.DataFrame(dict(text=['zzzheldoutonly good'],split=['test'],rating=[999]))
    pipeline.transform(held)
    assert 'zzzheldoutonly' not in pipeline.vectorizer.vocabulary_
    assert np.array_equal(before,pipeline.vectorizer.idf_)
    changed=train.copy();changed['rating']=[5,1];changed['sentiment']=['positive','negative']
    assert (pipeline.transform(train)!=pipeline.transform(changed)).nnz==0
    with pytest.raises(ValueError,match='refit'):pipeline.fit_train(train)
    with pytest.raises(ValueError,match='train-only'):ClassicalPreprocessor(min_df=1).fit_train(held)
    path=tmp_path/'fixture.joblib';joblib.dump(pipeline,path)
    assert (joblib.load(path).transform(train)!=matrix).nnz==0
    assert pipeline.fit_id_sha256==ordered_id_digest(['b','a'])


@pytest.fixture
def tokenizer_file(tmp_path):
    vocab={token:i for i,token in enumerate(['[PAD]','[UNK]','[CLS]','[SEP]','[MASK]',
                                          'not','never','no','great','bad','!','?','don',"'",'t'])}
    tokenizer=Tokenizer(models.WordPiece(vocab=vocab,unk_token='[UNK]'))
    tokenizer.normalizer=normalizers.BertNormalizer(lowercase=True)
    tokenizer.pre_tokenizer=pre_tokenizers.BertPreTokenizer()
    tokenizer.post_processor=processors.TemplateProcessing(single='[CLS] $A [SEP]',
                                                           special_tokens=[('[CLS]',2),('[SEP]',3)])
    path=tmp_path/'synthetic_tokenizer.json';tokenizer.save(str(path));return path


def test_bert_real_encoder_contract_negation_truncation_padding_reload(tokenizer_file,tmp_path):
    base=BertPreprocessor(tokenizer_file)
    frame=pd.DataFrame({'text':['NOT never no!', 'great '*100]})
    assert base.lengths(frame)==[6,102]
    max_length,policy=choose_max_length(base.lengths(frame),candidates=(8,16),quantile=.5)
    assert max_length==16 and policy['selection_split']=='train'
    bert=BertPreprocessor(tokenizer_file,max_length=8)
    encoded=bert.encode(frame)
    assert encoded[0]['input_ids']==[2,5,6,7,10,3]
    assert len(encoded[1]['input_ids'])==8 and encoded[1]['input_ids'][-1]==3
    padded=bert.encode(frame,padding=True)
    assert padded[0]['attention_mask']==[1]*6+[0]*2
    assert len(padded[0]['input_ids'])==len(padded[1]['input_ids'])==8
    output=tmp_path/'export.json';bert.tokenizer.save(str(output))
    assert BertPreprocessor(output,max_length=8).encode(frame)==encoded
    assert set(encoded[0])=={'input_ids','attention_mask','token_type_ids'}


def test_fixed_normalization_rejects_empty_and_preserves_sentiment():
    raw="<p>NOT never no don't!!!</p> 😀\n  Great?"
    assert minimal_text(raw)=="NOT never no don't!!! 😀 Great?"
    assert classical_text(raw)=="not never no don't!!! 😀 great?"
    assert minimal_text(minimal_text(raw))==minimal_text(raw)
    with pytest.raises(ValueError):minimal_text(' <br> ')
    with pytest.raises(ValueError):minimal_text(None)


def test_bert_length_rule_training_observations_only():
    length,info=choose_max_length([64,64,128,128],quantile=.95)
    assert length==128 and info['train_truncation_share']==0
    length,info=choose_max_length([900,1100])
    assert length==512 and info['train_truncation_share']==1
    with pytest.raises(ValueError):choose_max_length([])
    with pytest.raises(ValueError):choose_max_length([0])
