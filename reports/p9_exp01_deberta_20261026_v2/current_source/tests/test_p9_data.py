"""Fixtures tổng hợp ASC/joint matching; không phải annotation thật hoặc model score."""
import copy
import json

import pytest

from src.absa.sentiment_data import (asc_tokenizer,build_asc_samples,encode_aspect,load_p9_config,
    marked_input,resolve_aspect_span)
from src.config import PROJECT_ROOT
from src.evaluation.aspect_sentiment import asc_error_analysis,joint_metrics
from src.evaluation.classification import LABELS,classification_metrics


@pytest.fixture
def tokenizer():
    return asc_tokenizer(PROJECT_ROOT/'artifacts/preprocessing/p4_20261009_final/bert/tokenizer.json')


def fixture_row(text='battery good but battery bad.',spans=None):
    spans=spans or [(0,7,'positive'),(17,24,'negative')]
    return {'uid':'train:fixture','sentence_id':'fixture','split':'train','original_split':'train',
            'source_file':'fixture.xml','text':text,
            'aspects':[{'term':text[a:b],'start':a,'end':b,'polarity':p,
                        'xml_attributes':{'term':text[a:b],'from':str(a),'to':str(b),'polarity':p}} for a,b,p in spans]}


def test_gold_aspect_samples_keep_occurrence_polarity_and_opposite_labels(tokenizer):
    row=fixture_row(); before=copy.deepcopy(row)
    samples,excluded,stats=build_asc_samples([row],tokenizer,128)
    assert not excluded and stats['examples']==2 and row==before
    assert [r['label_id'] for r in samples]==[2,0]
    assert [r['start'] for r in samples]==[0,17]
    assert samples[0]['input_ids']!=samples[1]['input_ids']
    assert samples[0]['marked_text'].startswith('[unused0]battery[unused1]')
    assert samples[1]['marked_text'].startswith('battery good but [unused0]battery[unused1]')
    assert [r['original_aspect'] for r in samples]==row['aspects']


def test_conflict_is_excluded_with_original_metadata_never_neutral(tokenizer):
    row=fixture_row('screen battery',[(0,6,'conflict'),(7,14,'neutral')])
    samples,excluded,stats=build_asc_samples([row],tokenizer,128)
    assert len(samples)==len(excluded)==1
    assert samples[0]['label']=='neutral' and samples[0]['label_id']==1
    assert excluded[0]['original_polarity']=='conflict' and 'label_id' not in excluded[0]
    assert excluded[0]['original_aspect']==row['aspects'][0]
    assert stats['original_polarity_counts']['conflict']==1


@pytest.mark.parametrize('fault',['polarity','missing','span','duplicate','id'])
def test_bad_polarity_or_annotation_rejected(tokenizer,fault):
    row=fixture_row()
    if fault=='polarity': row['aspects'][0]['polarity']='unknown'
    if fault=='missing': row['aspects'][0].pop('polarity')
    if fault=='span': row['aspects'][0]['end']=999
    if fault=='duplicate': row['aspects'].append(copy.deepcopy(row['aspects'][0]))
    if fault=='id': row['uid']='test:wrong'
    with pytest.raises(ValueError): build_asc_samples([row],tokenizer,128)


def test_markers_reserved_ids_and_tokenizer_serialization(tokenizer,tmp_path):
    assert tokenizer.get_vocab_size()==30522
    encoded=encode_aspect('keyboard, battery!','battery',10,17,tokenizer,128)
    assert encoded['input_ids'].count(1)==encoded['input_ids'].count(2)==1
    path=tmp_path/'tokenizer.json'; tokenizer.save(str(path))
    restored=asc_tokenizer(path)
    assert restored.encode(encoded['marked_text']).ids==encoded['input_ids']
    assert encoded['tokens'][encoded['input_ids'].index(1)]=='[unused0]'


def test_api_repeated_term_needs_offsets_and_empty_or_bad_offsets_rejected():
    with pytest.raises(ValueError): resolve_aspect_span('battery and battery','battery',None,None)
    assert resolve_aspect_span('good battery','battery',None,None)==(5,12)
    assert resolve_aspect_span('battery and battery','battery',12,19)==(12,19)
    with pytest.raises(ValueError): resolve_aspect_span('banana','ana',None,None)
    with pytest.raises(ValueError): resolve_aspect_span('battery','battery',0,None)
    with pytest.raises(ValueError): marked_input('battery','screen',0,7)
    with pytest.raises(ValueError): marked_input('[unused0]battery','battery',9,16)


def test_overlength_never_truncates_aspect(tokenizer):
    with pytest.raises(ValueError,match='không truncate'):
        encode_aspect('battery '*100,'battery',0,7,tokenizer,16)


def test_three_class_mapping_and_metrics_confusion():
    assert LABELS==('negative','neutral','positive')
    metric=classification_metrics([0,1,2],[0,2,2])
    assert metric['accuracy']==pytest.approx(2/3)
    assert metric['confusion_matrix']==[[1,0,0],[0,0,1],[0,0,1]]
    assert metric['macro_f1']==pytest.approx((1+0+2/3)/3)


def test_joint_boundary_sentiment_and_conflict_are_separate():
    text='battery life keyboard screen'
    gold=[{'term':text[a:b],'start':a,'end':b,'polarity':p} for a,b,p in [(0,12,'positive'),(13,21,'negative'),(22,28,'conflict')]]
    pred=[{'term':text[a:b],'start':a,'end':b,'sentiment':p} for a,b,p in [(0,7,'positive'),(13,21,'positive'),(22,28,'negative')]]
    m=joint_metrics([{'uid':'fixture:1','text':text,'gold_aspects':gold,'predicted_aspects':pred}])
    c=m['counts']
    assert m['f1']==0 and c['false_negative']==c['false_positive']==2
    assert c['conflict_gold_excluded']==c['predictions_ignored_exact_conflict']==1
    assert c['extraction_missing_gold_spans']==c['extraction_spurious_predicted_spans']==1
    assert c['sentiment_errors_on_exact_span']==1 and c['boundary_pairs']==1
    assert c['joint_wrong_span_and_polarity_pairs']==0


def test_joint_partial_credit_not_allowed_and_empty_predictions():
    row={'uid':'x','text':'battery good','gold_aspects':[{'term':'battery','start':0,'end':7,'polarity':'positive'}],
         'predicted_aspects':[{'term':'battery','start':0,'end':7,'sentiment':'positive'},
                              {'term':'good','start':8,'end':12,'sentiment':'positive'}]}
    m=joint_metrics([row]);assert m['precision']==.5 and m['recall']==1 and m['f1']==pytest.approx(2/3)
    row['predicted_aspects']=[];m=joint_metrics([row]);assert m['f1']==0 and m['counts']['false_negative']==1


def test_error_groups_are_descriptive_with_correct_denominators():
    r={'sentence_uid':'s','text':'battery is not good but screen is better','aspect':'battery','label':'negative',
       'label_id':0,'predicted_label_id':2,'correct':False}
    s={**r,'aspect':'screen','label':'positive','label_id':2,'predicted_label_id':2,'correct':True}
    a=asc_error_analysis([r,s],{'battery':2,'screen':1})
    groups={g['group']:g for g in a['groups']}
    assert groups['mixed_polarity_sentence']['examples']==2 and groups['mixed_polarity_sentence']['errors']==1
    assert groups['negation_cue']['accuracy']==.5
    assert groups['rare_aspect_train_frequency_le1']['examples']==1


def test_p9_reuses_exact_p8_sentence_split_and_train_only_weights():
    cfg=load_p9_config()
    manifest=json.loads((PROJECT_ROOT/cfg['data_directory']/'manifest.json').read_text(encoding='utf-8'))
    p8=json.loads((PROJECT_ROOT/cfg['p8_manifest']).read_text(encoding='utf-8'))
    assert manifest['sentence_split_ids']==p8['split_ids']
    counts=manifest['splits']['train']['class_counts']; n=sum(counts.values())
    for label in LABELS: assert manifest['balanced_weights_train_only'][label]==n/(3*counts[label])
    assert manifest['leakage']['train_validation_normalized_text_overlap']==0


def test_real_asc_records_preserve_polarity_and_auditable_conflict_exclusions():
    from src.absa.extraction_data import load_records
    from src.absa.sentiment_data import load_asc_records
    cfg=load_p9_config(); manifest=json.loads((PROJECT_ROOT/cfg['data_directory']/'manifest.json').read_text(encoding='utf-8'))
    p8=json.loads((PROJECT_ROOT/cfg['p8_manifest']).read_text(encoding='utf-8'))
    for split in ['train','validation','test']:
        original={r['uid']:r for r in load_records(PROJECT_ROOT,p8,split)}
        rows=load_asc_records(PROJECT_ROOT,manifest,split)
        excluded=[json.loads(line) for line in (PROJECT_ROOT/manifest['excluded_files'][split]['path']).read_text(encoding='utf-8').splitlines()]
        assert len(rows)+len(excluded)==manifest['splits'][split]['original_aspect_entities']
        assert len({r['example_id'] for r in rows+excluded})==len(rows)+len(excluded)
        for r in rows+excluded:
            assert r['original_aspect']==original[r['sentence_uid']]['aspects'][r['original_aspect_index']]
            assert r['aspect']==r['text'][r['start']:r['end']]
        assert all(r['original_polarity']=='conflict' and 'label_id' not in r for r in excluded)
        assert all(r['label']==r['original_polarity']==LABELS[r['label_id']] for r in rows)


@pytest.mark.parametrize('fault',['id','gold','label','correct'])
def test_saved_asc_prediction_integrity_rejects_corruption(fault):
    from src.absa.sentiment_data import load_asc_records
    from scripts.finalize_p9 import verify_asc_predictions
    cfg=load_p9_config(); manifest=json.loads((PROJECT_ROOT/cfg['data_directory']/'manifest.json').read_text(encoding='utf-8'))
    rows=load_asc_records(PROJECT_ROOT,manifest,'validation')
    pred=[json.loads(line) for line in (PROJECT_ROOT/cfg['prediction_directory']/'validation_predictions.jsonl').read_text(encoding='utf-8').splitlines()]
    assert verify_asc_predictions(rows,pred)['per_class']['neutral']['support']==manifest['splits']['validation']['class_counts']['neutral']
    if fault=='id': pred[0]['example_id']='wrong'
    if fault=='gold': pred[0]['original_polarity']='conflict'
    if fault=='label': pred[0]['predicted_label_id']=3
    if fault=='correct': pred[0]['correct']=not pred[0]['correct']
    with pytest.raises(ValueError): verify_asc_predictions(rows,pred)


def test_saved_joint_decomposition_and_no_dropping_p8_spans():
    from src.absa.extraction_data import load_records
    from scripts.finalize_p9 import verify_joint_predictions
    cfg=load_p9_config();p8=json.loads((PROJECT_ROOT/cfg['p8_manifest']).read_text(encoding='utf-8'))
    rows=load_records(PROJECT_ROOT,p8,'validation')
    extracted=[json.loads(line) for line in (PROJECT_ROOT/cfg['p8_predictions']/'validation_predictions.jsonl').read_text(encoding='utf-8').splitlines()]
    pred=[json.loads(line) for line in (PROJECT_ROOT/cfg['prediction_directory']/'validation_end_to_end_predictions.jsonl').read_text(encoding='utf-8').splitlines()]
    m=verify_joint_predictions(rows,extracted,pred);c=m['counts']
    assert c['false_negative']==c['extraction_missing_gold_spans']+c['sentiment_errors_on_exact_span']
    assert c['false_positive']==c['extraction_spurious_predicted_spans']+c['sentiment_errors_on_exact_span']
    next(r for r in pred if r['predicted_aspects'])['predicted_aspects'].pop()
    with pytest.raises(ValueError): verify_joint_predictions(rows,extracted,pred)
def test_paired_backbone_predictions_require_same_gold_and_ids():
    from src.evaluation.asc_comparison import paired_predictions
    baseline=[]; candidate=[]
    for i,(old,new) in enumerate([(0,1),(1,0),(0,0),(1,1)]):
        row={'example_id':str(i),'text':'fixture','aspect':'fixture','start':0,'end':7,
             'label_id':1,'label':'neutral','sentence_uid':'train:fixture'}
        baseline.append({**row,'predicted_label_id':old,'correct':old==1})
        candidate.append({**row,'predicted_label_id':new,'correct':new==1})
    counts,_=paired_predictions(baseline,candidate)
    assert counts=={'fixed':1,'regressed':1,'both_correct':1,'both_wrong':1}
    with pytest.raises(ValueError,match='ID/order'): paired_predictions(baseline,candidate[::-1])
    candidate[0]['start']=1
    with pytest.raises(ValueError,match='gold/context'): paired_predictions(baseline,candidate)

