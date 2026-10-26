"""Fixtures tổng hợp cho chẩn đoán; không phải review/nhãn gold thật."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.evaluation.error_diagnosis import error_tables,imbalance_evidence,load_predictions,file_hash
from src.evaluation.sentiment_audit import (prepare_audit,sample_audit,read_annotations,evaluate_audit,FIXED,HUMAN)
from src.evaluation.classification import classification_metrics,LABELS


@pytest.fixture
def fixture_frames():
    frame=pd.DataFrame({'review_id':[f'fixture-{i}' for i in range(30)],'label_id':[i//10 for i in range(30)],
                        'rating':[2]*10+[3]*10+[5]*10,'review_title':['Fixture']*30,
                        'text':['not good and broken']*30,'language':['en']*30})
    pred=(frame.label_id.to_numpy()+1)%3
    return frame,{'E00_majority':np.full(30,2),'E01_fixture':pred,'E02_fixture':pred.copy()}


def test_error_support_denominators_and_active_examples(fixture_frames):
    frame,pred=fixture_frames;tables=error_tables(frame,pred)
    transitions=tables['transitions']
    for model in pred:
        sub=transitions[transitions.model==model]
        assert sub['count'].sum()==30 and len(sub)==9
        assert np.isclose(sub.groupby('proxy_label_id').rate_within_source_class.sum(),1).all()
    neutral=tables['classes'].query("model=='E01_fixture' and `class`=='neutral'").iloc[0]
    assert neutral.support==10 and neutral.proxy_disagreements==10 and neutral.error_rate_within_class==1
    assert tables['agreement'].support.sum()==30
    assert tables['review_predictions'].competitive_disagreement_count.eq(2).all()
    assert tables['examples'].human_verified.eq(False).all()
    assert tables['examples'].confidence.isna().all()


def test_load_predictions_rejects_row_shuffle(tmp_path,fixture_frames):
    frame,pred=fixture_frames
    folder=tmp_path/'reports/semantic_20261024/E01_fixture';folder.mkdir(parents=True)
    p=pd.DataFrame({'review_id':frame.review_id,'label_id':frame.label_id,'prediction_id':pred['E01_fixture']})
    p.to_parquet(folder/'test_predictions.parquet',index=False)
    score=classification_metrics(p.label_id,p.prediction_id)['macro_f1']
    pd.DataFrame([{'model':'E01_fixture','macro_f1':score,'train_samples':30,'data_regime':'FULL'}]).to_csv(tmp_path/'reports/p7_unified_results.csv',index=False)
    loaded,_=load_predictions(tmp_path,frame,{'models':['E01_fixture']})
    assert np.array_equal(loaded['E01_fixture'],pred['E01_fixture'])
    p.iloc[::-1].to_parquet(folder/'test_predictions.parquet',index=False)
    with pytest.raises(ValueError,match='ID/order'):load_predictions(tmp_path,frame,{'models':['E01_fixture']})


def test_weighted_epoch_selection_uses_macro_not_neutral(fixture_frames):
    frame,pred=fixture_frames
    m=classification_metrics(frame.label_id,pred['E01_fixture'])
    history=[]
    for mode in ['unweighted','balanced']:
        for epoch,macro,neutral in [(1,.7,.9),(2,.8,.1)]:
            values=json.loads(json.dumps(m));values['macro_f1']=macro;values['per_class']['neutral']['f1']=neutral
            history.append({'mode':mode,'epoch':epoch,'validation':values})
    dist,comparison=imbalance_evidence({'train':frame,'test':frame},history)
    assert comparison[comparison.selected_within_mode_by_validation_macro_f1].epoch.tolist()==[2,2]
    assert np.allclose(dist.inverse_frequency_weight_train,1)


@pytest.fixture
def fixture_kit(tmp_path,fixture_frames):
    frame,pred=fixture_frames;wide=error_tables(frame,pred)['review_predictions']
    kit=tmp_path/'kit';inputs={'fixture':'no_real_labels'}
    manifest=prepare_audit(frame,wide,kit,inputs,representative_n=6,diagnostic_per_class=2)
    return kit,frame,wide,inputs,manifest


def test_audit_sampling_blind_and_disjoint(fixture_kit):
    kit,frame,wide,inputs,manifest=fixture_kit
    refs=json.loads((kit/'private_reference.json').read_text(encoding='utf-8'))
    rows=pd.read_csv(kit/'review_annotation.csv',keep_default_na=False)
    assert len(rows)==12 and rows[HUMAN].eq('').all().all()
    assert list(rows.columns)==FIXED+HUMAN
    assert not {'rating','y_true','y_pred','sampling_group','review_id'} & set(rows.columns)
    assert len({r['review_id'] for r in refs})==12
    assert sum(r['sampling_group']=='representative' for r in refs)==6
    assert all(r['inclusion_probability']==6/30 for r in refs if r['sampling_group']=='representative')
    assert sample_audit(frame,wide,representative_n=6,diagnostic_per_class=2)==sample_audit(frame,wide,representative_n=6,diagnostic_per_class=2)
    assert manifest['human_labels_created_by_codex'] is False


def test_audit_rerun_preserves_human_input(fixture_kit):
    kit,frame,wide,inputs,_=fixture_kit
    p=kit/'review_annotation.csv';rows=pd.read_csv(p,keep_default_na=False)
    rows.loc[0,'human_sentiment']='uncertain';rows.to_csv(p,index=False)
    before=file_hash(p)
    prepare_audit(frame,wide,kit,inputs,representative_n=6,diagnostic_per_class=2)
    assert file_hash(p)==before


@pytest.mark.parametrize('fault',['label','text','id','sidecar'])
def test_audit_validator_rejects_invalid_or_changed_data(fixture_kit,fault):
    kit,*_=fixture_kit;p=kit/'review_annotation.csv';rows=pd.read_csv(p,keep_default_na=False)
    if fault=='label':rows.loc[0,'human_sentiment']='mixed'
    if fault=='text':rows.loc[0,'review_text']='modified fixture'
    if fault=='id':rows.loc[0,'annotation_id']=rows.loc[1,'annotation_id']
    if fault=='sidecar':(kit/'private_reference.json').write_text('[]',encoding='utf-8')
    else:rows.to_csv(p,index=False)
    with pytest.raises(ValueError):read_annotations(kit,require_complete=False)


def test_audit_requires_human_confirmation_and_complete_labels(fixture_kit):
    kit,*_=fixture_kit
    with pytest.raises(ValueError,match='xác nhận'):evaluate_audit(kit)
    with pytest.raises(ValueError,match='PENDING'):evaluate_audit(kit,confirmed_human_review=True)


def test_fixture_human_comparison_never_pools_enriched_or_converts_uncertain(fixture_kit):
    kit,*_=fixture_kit
    rows=pd.read_csv(kit/'review_annotation.csv',keep_default_na=False)
    refs=json.loads((kit/'private_reference.json').read_text(encoding='utf-8'))
    lookup={r['annotation_id']:r for r in refs}
    uncertain_id=next(r['annotation_id'] for r in refs if r['sampling_group']=='representative')
    for i,row in rows.iterrows():
        ref=lookup[row.annotation_id]
        # Nhãn chỉ cho fixture; không ghi vào dữ liệu audit thật.
        rows.loc[i,'human_sentiment']='uncertain' if row.annotation_id==uncertain_id else LABELS[(ref['proxy_label_id']+1)%3]
        rows.loc[i,'ambiguity']='mixed';rows.loc[i,'evidence']='Fixture evidence'
        rows.loc[i,'reviewer_id']='fixture_reviewer';rows.loc[i,'reviewed_at']='2026-10-24T10:00:00+07:00'
    rows.to_csv(kit/'review_annotation.csv',index=False)
    result=evaluate_audit(kit,confirmed_human_review=True)
    rep=result['groups']['representative'];diag=result['groups']['diagnostic_enriched']
    assert rep['audited_n']==6 and rep['decisive_n']==5 and rep['uncertain_n']==1
    assert rep['proxy_human_mismatches']==5
    assert 'test_population_proxy_mismatch_95pct_interval' not in rep
    assert diag['population_estimate_allowed'] is False
    assert rep['models']['E01_fixture']['diagnostic_counts']['proxy_mismatch_model_matches_human']==5
    assert result['imbalance_causal_attribution']=='NOT_IDENTIFIABLE_FROM_THIS_AUDIT'


def test_current_six_models_use_cloud_and_unchanged_scores():
    from src.config import PROJECT_ROOT
    completion=json.loads((PROJECT_ROOT/'reports/p7_completion.json').read_text(encoding='utf-8'))
    frame=pd.read_parquet(PROJECT_ROOT/'data/processed/splits/p4_20261009_final/test.parquet')
    predictions,source=load_predictions(PROJECT_ROOT,frame,completion)
    assert len(predictions)==6
    assert source['E03_tabpfn_v3_embedding']['train_samples']==21000
    assert source['E04_tabpfn_v35_embedding']['path'].endswith('tabpfn_v35_full21k/test_predictions.csv')
    stats=pd.read_csv(PROJECT_ROOT/'reports/p7_class_diagnostics.csv')
    assert stats.query("model=='E03_tabpfn_v3_embedding' and `class`=='neutral'").predicted_count.item()==8


def test_fixture_decisive_audit_reports_interval_and_model_errors(fixture_kit):
    kit,*_=fixture_kit
    rows=pd.read_csv(kit/'review_annotation.csv',keep_default_na=False)
    refs={r['annotation_id']:r for r in json.loads((kit/'private_reference.json').read_text(encoding='utf-8'))}
    for i,row in rows.iterrows():
        rows.loc[i,'human_sentiment']=LABELS[refs[row.annotation_id]['proxy_label_id']]
        rows.loc[i,'ambiguity']='clear';rows.loc[i,'evidence']='Fixture only'
        rows.loc[i,'reviewer_id']='fixture_reviewer';rows.loc[i,'reviewed_at']='2026-10-24'
    rows.to_csv(kit/'review_annotation.csv',index=False)
    rep=evaluate_audit(kit,confirmed_human_review=True)['groups']['representative']
    assert rep['proxy_human_mismatches']==0 and rep['uncertain_n']==0
    assert rep['test_population_proxy_mismatch_95pct_interval'][0]==0
    assert rep['models']['E01_fixture']['diagnostic_counts']['model_error_with_proxy_agreement']==6


def test_weighting_pairs_partition_and_false_positives():
    from src.evaluation.error_diagnosis import weighting_pairs
    truth=np.array([0,0,1,1,2,2])
    old=np.array([0,1,1,2,2,0]);new=np.array([1,0,1,1,2,2])
    pairs=weighting_pairs(truth,old,new)
    assert np.array_equal(pairs[['both_correct','corrected_by_balanced','regressed_by_balanced','both_wrong']].sum(axis=1),pairs.support)
    neutral=pairs[pairs['class']=='neutral'].iloc[0]
    assert neutral.corrected_by_balanced==1 and neutral.both_correct==1
    assert neutral.unweighted_false_positives==1 and neutral.balanced_false_positives==1


def test_diagnosis_cli_help_works_with_windows_pipe(tmp_path):
    import os,subprocess,sys
    from src.config import PROJECT_ROOT
    env={**os.environ,'PYTHONIOENCODING':'cp1252'}
    result=subprocess.run([sys.executable,'-B','-m','scripts.analyze_error_causes','--help'],cwd=PROJECT_ROOT,env=env,capture_output=True)
    assert result.returncode==0
    assert '--confirm-human-review' in result.stdout.decode('utf-8')
