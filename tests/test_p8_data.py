"""Fixtures tổng hợp cho offsets/BIO/metric; không thay annotation SemEval thật."""
import copy
import json

import pytest

from src.absa.extraction_data import (LABELS,canonical_aspects,decode_bio,encode_sentence,
    load_tokenizer,split_train_validation,validate_bio)
from src.config import PROJECT_ROOT
from src.evaluation.aspect_extraction import entity_metrics,error_analysis


@pytest.fixture
def tokenizer():
    return load_tokenizer(PROJECT_ROOT/'artifacts/preprocessing/p4_20261009_final/bert/tokenizer.json')


def row(text,spans):
    return {'source':'semeval2014_laptop','split':'train','sentence_id':'fixture-001','text':text,
            'aspects':[{'term':text[a:b],'start':a,'end':b,'polarity':'conflict',
                        'xml_attributes':{'from':str(a),'to':str(b)}} for a,b in spans]}


@pytest.mark.parametrize('text,spans',[
    ('battery works.',[(0,7)]),
    ('The battery life is good.',[(4,16)]),
    ('battery good; keyboard bad.',[(0,7),(14,22)]),
    ('Everything works.',[]),
    ('battery and battery.',[(12,19)]),
    ('electroencephalography works.',[(0,22)]),
    ('A securitysoftware issue.',[(2,18)]),
])
def test_bio_offsets_roundtrip_and_original_metadata(tokenizer,text,spans):
    original=row(text,spans); before=copy.deepcopy(original)
    encoded,changes=encode_sentence(original,tokenizer,split='train',max_length=128,source_file='fixture.xml')
    assert original==before and encoded['aspects']==original['aspects']
    assert encoded['sentence_id']=='fixture-001' and encoded['uid']=='train:fixture-001'
    assert not changes
    assert encoded['labels'][0]==encoded['labels'][-1]==-100
    decoded=decode_bio(text,encoded['offsets'],encoded['labels'],strict=True)
    assert [(a['start'],a['end']) for a in decoded]==spans
    if 'electroencephalography' in text:
        assert encoded['labels'].count(2)>0
    if not spans: assert set(encoded['labels'])=={-100,0}


def test_boundary_whitespace_adjustment_is_explicit_and_lossless(tokenizer):
    original=row('A battery\u00a0 works.',[(2,10)])
    encoded,changes=encode_sentence(original,tokenizer,split='validation',max_length=128,source_file='fixture.xml')
    assert encoded['aspects'][0]['term']=='battery\u00a0'
    assert encoded['aspects'][0]['end']==10
    assert encoded['extraction_aspects'][0]['term']=='battery'
    assert changes[0]['original_span']==[2,10] and changes[0]['extraction_span']==[2,9]


@pytest.mark.parametrize('fault',['missing_id','out_of_range','mismatch','empty','overlap','duplicate'])
def test_invalid_aspects_rejected(fault):
    r=row('battery life',[(0,7)])
    if fault=='missing_id': r['sentence_id']=''
    if fault=='out_of_range': r['aspects'][0]['end']=99
    if fault=='mismatch': r['aspects'][0]['term']='wrong'
    if fault=='empty': r['aspects'][0].update(term='',end=0)
    if fault=='overlap': r['aspects'].append({'term':'battery life','start':0,'end':12})
    if fault=='duplicate': r['aspects'].append(copy.deepcopy(r['aspects'][0]))
    with pytest.raises(ValueError): canonical_aspects(r)


def test_no_silent_truncation(tokenizer):
    with pytest.raises(ValueError,match='không truncate'):
        encode_sentence(row('battery '*30,[(0,7)]),tokenizer,split='train',max_length=8,source_file='fixture.xml')


def test_bio_invalid_transition_and_orphan_repair():
    with pytest.raises(ValueError): validate_bio([-100,0,2,-100])
    assert decode_bio('battery life',[(0,7),(8,12)],[2,2])==[
        {'term':'battery life','start':0,'end':12,'score':None}]
    with pytest.raises(ValueError): decode_bio('abc',[(0,3)],[])
    with pytest.raises(ValueError): decode_bio('abc',[(0,4)],[1])


def test_grouped_train_validation_is_deterministic_and_test_rejected():
    rows=[{'split':'train','sentence_id':str(i),'text':f'group {i//2}'} for i in range(30)]
    a=split_train_validation(rows,seed=42,fraction=.2)
    assert a==split_train_validation(list(reversed(rows)),seed=42,fraction=.2)
    assert not {r['text'] for r in a['train']}&{r['text'] for r in a['validation']}
    assert sum(map(len,a.values()))==30
    rows[0]['split']='test'
    with pytest.raises(ValueError): split_train_validation(rows,seed=42,fraction=.2)


def test_strict_entity_metric_partial_boundary_is_wrong_and_errors_overlap():
    text='battery life keyboard wrong'
    aspect=lambda a,b:{'term':text[a:b],'start':a,'end':b}
    records=[{'uid':'fixture:1','sentence_id':'1','text':text,
              'gold_aspects':[aspect(0,12),aspect(13,21)],
              'predicted_aspects':[aspect(0,7),aspect(13,21),aspect(22,27)]},
             {'uid':'fixture:2','sentence_id':'2','text':'Fine.', 'gold_aspects':[],'predicted_aspects':[]}]
    metrics=entity_metrics(records)
    assert metrics['true_positive']==1 and metrics['false_positive']==2 and metrics['false_negative']==1
    assert metrics['entity_precision']==pytest.approx(1/3)
    assert metrics['entity_recall']==.5 and metrics['entity_f1']==pytest.approx(.4)
    analysis=error_analysis(records,{'battery life':1,'keyboard':3})
    assert analysis['counts']['boundary_pairs']==1
    assert analysis['counts']['multiword_missed']==1 and analysis['counts']['rare_missed']==1
    assert analysis['counts']['false_positive_without_overlap']==1


def test_empty_predictions_no_aspect_and_duplicate_ids():
    r={'uid':'x','sentence_id':'x','text':'fine','gold_aspects':[],'predicted_aspects':[]}
    assert entity_metrics([r])['entity_f1']==0
    with pytest.raises(ValueError): entity_metrics([r,r])


def test_prepared_real_records_preserve_original_spans_ids_and_polarity():
    from src.absa.extraction_data import load_records,load_p8_config
    from src.data.semeval import read_semeval_sentences
    cfg=load_p8_config()
    manifest=json.loads((PROJECT_ROOT/cfg['data_directory']/'manifest.json').read_text(encoding='utf-8'))
    originals={f"{split}:{r['sentence_id']}":r for split in ['train','test']
               for r in read_semeval_sentences(PROJECT_ROOT/cfg['sources'][split+'_xml'],split)}
    seen=set(); texts={}
    for split in ['train','validation','test']:
        records=load_records(PROJECT_ROOT,manifest,split)
        assert len(records)==manifest['splits'][split]['sentences']
        assert not seen & {r['uid'] for r in records}
        seen.update(r['uid'] for r in records)
        texts[split]={' '.join(r['text'].casefold().split()) for r in records}
        for r in records:
            assert r['aspects']==originals[r['uid']]['aspects']
            assert r['text']==originals[r['uid']]['text']
            assert r['sentence_id']==originals[r['uid']]['sentence_id']
    assert len(seen)==len(originals)
    assert not texts['train'] & texts['validation']
    assert len(texts['test'] & (texts['train']|texts['validation']))==1


@pytest.mark.parametrize('fault',['uid','text','gold','decode'])
def test_saved_prediction_verification_rejects_corruption(fault):
    from src.absa.extraction_data import load_records,load_p8_config
    from scripts.finalize_p8 import verify_predictions
    cfg=load_p8_config()
    manifest=json.loads((PROJECT_ROOT/cfg['data_directory']/'manifest.json').read_text(encoding='utf-8'))
    records=load_records(PROJECT_ROOT,manifest,'validation')
    predictions=[json.loads(line) for line in (PROJECT_ROOT/cfg['prediction_directory']/'validation_predictions.jsonl').read_text(encoding='utf-8').splitlines()]
    assert verify_predictions(records,predictions)['sentences']==len(records)
    if fault=='uid': predictions[0]['uid']='corrupted'
    if fault=='text': predictions[0]['text']='corrupted'
    if fault=='gold': predictions[0]['gold_aspects']=[{'term':'invalid','start':0,'end':7}]
    if fault=='decode': predictions[0]['predicted_label_ids']=[]
    with pytest.raises(ValueError): verify_predictions(records,predictions)
