"""Fixtures tổng hợp kiểm số học diagnosis; không tạo annotation người thật."""
import json

import pandas as pd
import pytest

from src.evaluation.human_diagnosis import attribution_case, compare_rows, markdown_table, validate_sources
from src.evaluation.sentiment_audit import ambiguity_flag, read_annotations


@pytest.mark.parametrize('human,proxy,pred,case', [
    (0,1,0,'A'), (0,1,1,'B'), (0,0,2,'C'), (0,1,2,'D'), (0,0,0,'E')])
def test_exclusive_cases(human,proxy,pred,case):
    assert attribution_case(human,proxy,pred)==case


def test_proxy_metrics_attribution_and_denominators():
    rows=pd.DataFrame({'human_id':[0,0,0,0,0], 'proxy_label_id':[1,1,0,1,0],
                       'Efixture':[0,1,2,2,0], 'ambiguous':[True,True,False,True,False],
                       'rating':[3,3,1,3,2]})
    result=compare_rows(rows,['Efixture'])
    assert result['agreement']==2 and result['disagreement']==3
    assert result['confusion_matrix_human_rows_proxy_columns']==[[2,3,0],[0,0,0],[0,0,0]]
    assert result['classes'][0]['disagreement_rate']==.6
    assert result['classes'][1]['disagreement_rate'] is None
    assert result['ambiguity'][0]['disagreement_rate']==0
    assert result['ambiguity'][1]['disagreement_rate']==1
    model=result['models']['Efixture']
    assert model['exclusive_cases']==dict.fromkeys('ABCDE',1)
    assert model['D_inclusive']==2 and model['human_errors']==3 and model['proxy_errors']==3
    assert model['human_metrics']['accuracy']==.4
    assert model['delta']['accuracy']==pytest.approx(0)
    assert model['human_metrics']['macro_f1']==pytest.approx((4/7)/3)
    assert sum(model['case_percentages'].values())==1
    assert '| n |' in markdown_table(pd.DataFrame([{'n':5}]))


def test_boolean_ambiguity_and_invalid_values():
    assert ambiguity_flag('TRUE') and ambiguity_flag('mixed')
    assert not ambiguity_flag('FALSE') and not ambiguity_flag('clear')
    with pytest.raises(ValueError): ambiguity_flag('probably')


def test_real_human_annotation_integrity_and_source_mapping():
    from src.config import PROJECT_ROOT
    kit=PROJECT_ROOT/'data/manual/sentiment_diagnosis_20261024'
    frame,_,_=read_annotations(kit)
    assert len(frame)==360 and frame.human_sentiment.isin(['negative','neutral','positive']).all()
    rows,integrity=validate_sources(PROJECT_ROOT,kit)
    assert integrity['status']=='PASS' and rows.annotation_id.is_unique
    assert rows.sampling_group.value_counts().to_dict()=={'representative':300,'diagnostic_enriched':60}


def test_generated_tables_match_source_metrics_and_exclusive_counts():
    from src.config import PROJECT_ROOT
    rows,integrity=validate_sources(PROJECT_ROOT,PROJECT_ROOT/'data/manual/sentiment_diagnosis_20261024')
    expected=compare_rows(rows,list(integrity['prediction_sources']))
    metrics=pd.read_csv(PROJECT_ROOT/'reports/p7_human_model_metrics.csv').query("scope=='all_360_descriptive_only'").set_index('model')
    cases=pd.read_csv(PROJECT_ROOT/'reports/p7_human_attribution.csv').query("scope=='all_360_descriptive_only'").set_index('model')
    for name,m in expected['models'].items():
        assert metrics.loc[name,'human_macro_f1']==pytest.approx(m['human_metrics']['macro_f1'],abs=1e-12)
        assert metrics.loc[name,'proxy_macro_f1']==pytest.approx(m['proxy_metrics']['macro_f1'],abs=1e-12)
        assert cases.loc[name,list('ABCDE')].sum()==len(rows)
        assert cases.loc[name,'human_errors']==m['human_errors']
    report=(PROJECT_ROOT/'reports/p7_error_cause_analysis.md').read_text(encoding='utf-8')
    assert all(f'## {i}.' in report for i in range(1,16))
    assert 'P7: DONE' in report and '**BLOCKED:** chưa có human sentiment annotations' not in report


@pytest.mark.parametrize('fault', ['missing', 'invalid_label', 'invalid_ambiguity', 'text', 'id', 'prediction'])
def test_real_integrity_rejects_mutated_copy(tmp_path,fault):
    from src.config import PROJECT_ROOT
    from src.evaluation.error_diagnosis import file_hash
    kit=PROJECT_ROOT/'data/manual/sentiment_diagnosis_20261024'
    for name in ['review_annotation.csv','manifest.json','private_reference.json']:
        (tmp_path/name).write_bytes((kit/name).read_bytes())
    f=pd.read_csv(tmp_path/'review_annotation.csv',dtype=str,keep_default_na=False)
    if fault=='missing': f.loc[0,'human_sentiment']=''
    if fault=='invalid_label': f.loc[0,'human_sentiment']='uncertain'
    if fault=='invalid_ambiguity': f.loc[0,'ambiguity']='maybe'
    if fault=='text': f.loc[0,'review_text']='Fixture modified'
    if fault=='id': f.loc[0,'annotation_id']=f.loc[1,'annotation_id']
    f.to_csv(tmp_path/'review_annotation.csv',index=False)
    if fault=='prediction':
        path=tmp_path/'private_reference.json'; refs=json.loads(path.read_text(encoding='utf-8'))
        model=next(iter(refs[0]['predictions']))
        refs[0]['predictions'][model]=(refs[0]['predictions'][model]+1)%3
        path.write_text(json.dumps(refs),encoding='utf-8')
        manifest=json.loads((tmp_path/'manifest.json').read_text(encoding='utf-8'))
        manifest['private_reference_sha256']=file_hash(path)
        (tmp_path/'manifest.json').write_text(json.dumps(manifest),encoding='utf-8')
    with pytest.raises(ValueError): validate_sources(PROJECT_ROOT,tmp_path)
