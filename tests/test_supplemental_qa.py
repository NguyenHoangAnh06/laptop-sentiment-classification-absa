"""Chỉ các thiết bị tổng hợp: nhãn bên dưới không phải là con người gán nhãn của hồ sơ thực."""
import json
from pathlib import Path
import pytest
from src.config import load_config
from src.data.acquisition import sha256_file
from src.data.independent_qa import (prepare_independent_qa,evaluate_independent_qa,
                                     read_csv,write_csv,HUMAN_COLUMNS)
from src.data.supplemental_qa import candidate_lines,prepare_supplemental_qa,evaluate_supplemental_qa


def fixture_pilot(tmp_path):
    raw,run,kit=tmp_path/'raw',tmp_path/'run',tmp_path/'v1'
    raw.mkdir();run.mkdir()
    acquisition=load_config('acquisition');limits=load_config('feasibility')['limits']
    keep=[{'parent_asin':f'K{i}','title':'Fixture laptop','categories':['Laptops']} for i in range(4)]
    reject=[{'parent_asin':f'R{i}','title':'Fixture laptop charger','categories':['Laptop Accessories']} for i in range(40)]
    rows=[{'parent_asin':f'K{i%4}' if i<8 else f'R{i%40}','text':'synthetic fixture text', 'title':'fixture','rating':5} for i in range(80)]
    inputs={}
    for kind,records in [('metadata',keep+reject),('reviews',rows)]:
        p=raw/f'{kind}.jsonl';p.write_text(''.join(json.dumps(r)+'\n' for r in records))
        h=sha256_file(p)
        Path(str(p)+'.manifest.json').write_text(json.dumps({'sha256':h,'source_url':acquisition['amazon'][f'{kind}_url'],'complete_source':True}))
        inputs[kind]={'name':p.name,'sha256':h}
    (run/'products.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in keep))
    saved=[{**r,'review_id':f"amazon2023:{inputs['reviews']['sha256']}:{i+1}",'source_line':i+1,
            'product_title':'Fixture laptop','review_title':r['title']} for i,r in enumerate(rows[:8])]
    (run/'laptop_valid.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in saved))
    report={'source':'Electronics','source_coverage_complete':True,'inputs':inputs,
            'output_sha256':{p.name:sha256_file(p) for p in run.iterdir()},
            'groups':{'laptop':{'candidate_products':4,'valid_reviews':8,'matched_reviews':8}},
            'review_scan':{'rows':80,'invalid_records':0},'metadata_scan':{'rows':44},
            'join_counts':{'not_in_selected_metadata_index':72}}
    (run/'report.json').write_text(json.dumps(report))
    prepare_independent_qa(run,raw,kit,acquisition,limits,product_n=2,boundary_n=2,review_n=2,diagnostic_n=0)
    refs={r['annotation_id']:r for r in json.loads((kit/'private_predictions.json').read_text())}
    for task in ('product','review'):
        p=kit/f'{task}_annotation.csv';columns,records=read_csv(p)
        for r in records:
            r['human_label']='laptop' if refs[r['annotation_id']]['prediction'] else 'non_laptop'
            r['human_evidence']='Synthetic test label only'
        p.unlink();write_csv(p,columns,records)
    e=evaluate_independent_qa(kit,{t:kit/f'{t}_annotation.csv' for t in ('product','review')},annotator='fixture',independent_human=True)
    (tmp_path/'pilot_evaluation').mkdir()
    evaluation=tmp_path/'pilot_evaluation/evaluation.json';evaluation.write_text(json.dumps(e))
    return run,raw,kit,evaluation,acquisition,limits


def test_uniform_candidate_mapping_and_reproducibility():
    lines=candidate_lines(10,{1,3,8},7,123)
    assert set(lines)=={2,4,5,6,7,9,10}
    assert lines==candidate_lines(10,{1,3,8},7,123)
    assert len(candidate_lines(100000000,{1,2,50},100,42))==100
    with pytest.raises(ValueError):candidate_lines(10,{0},2,3)
    with pytest.raises(ValueError):candidate_lines(10,{1},10,3)


def test_supplemental_fixture_reproducible_no_overlap_and_future_evaluation(tmp_path):
    args=fixture_pilot(tmp_path);out=tmp_path/'v2'
    before={p:sha256_file(p) for folder in args[:3] for p in folder.iterdir()}
    m=prepare_supplemental_qa(*args[:4],out,*args[4:],sample_size=6,seed=7)
    prepare_supplemental_qa(*args[:4],tmp_path/'v2_copy',*args[4:],sample_size=6,seed=7)
    assert (out/'review_annotation.csv').read_bytes()==(tmp_path/'v2_copy/review_annotation.csv').read_bytes()
    cols,rows=read_csv(out/'review_annotation.csv')
    assert len(rows)==6 and all(not r[c] for r in rows for c in HUMAN_COLUMNS)
    assert not {'prediction','stratum','sampling_weight'}&set(cols)
    _,old=read_csv(args[2]/'review_annotation.csv')
    assert not {r['review_id'] for r in rows}&{r['review_id'] for r in old}
    assert m['populations']['reject_complement']==70
    assert m['inclusion_probability']==pytest.approx(6/70)
    assert before=={p:sha256_file(p) for p in before}
    with pytest.raises(FileExistsError):prepare_supplemental_qa(*args[:4],out,*args[4:],sample_size=6)
    with pytest.raises(ValueError):evaluate_supplemental_qa(out,annotator='fixture',confirm_human=False)
    pending=evaluate_supplemental_qa(out,annotator='fixture',confirm_human=True)
    assert pending['combined_weighted_estimates'] is None and pending['pending_or_uncertain']==6
    for row in rows:row.update(human_label='non_laptop',human_evidence='Synthetic fixture verification')
    p=out/'review_annotation.csv';p.unlink();write_csv(p,cols,rows)
    result=evaluate_supplemental_qa(out,annotator='fixture',confirm_human=True,ai_assisted_review=True)
    assert result['combined_weighted_estimates']['confusion_matrix']['FN']==0
    assert result['combined_weighted_estimates']['intervals']['recall'][0]<1
    assert result['label_provenance']=='human_verified_after_ai_assistance'
    rows[0]['review_text']='tampered';p.unlink();write_csv(p,cols,rows)
    with pytest.raises(ValueError,match='Immutable'):evaluate_supplemental_qa(out,annotator='fixture',confirm_human=True)


def test_stale_pilot_and_output_protection(tmp_path):
    args=fixture_pilot(tmp_path)
    with pytest.raises(ValueError,match='separate'):
        prepare_supplemental_qa(*args[:4],args[0]/'newkit',*args[4:],sample_size=4)
    path=args[2]/'review_annotation.csv';path.write_bytes(path.read_bytes()+b'\n')
    with pytest.raises(ValueError,match='annotation changed'):
        prepare_supplemental_qa(*args[:4],tmp_path/'v2',*args[4:],sample_size=4)


def test_annotation_audit_rejects_aliases_and_detects_source_tampering(tmp_path):
    from scripts.validate_supplemental_annotations import audit_annotations
    args = fixture_pilot(tmp_path)
    out = tmp_path/'audit_v2'
    prepare_supplemental_qa(*args[:4], out, *args[4:], sample_size=6, seed=7)
    path = out/'review_annotation.csv'
    columns, rows = read_csv(path)
    for row in rows:
        row.update(human_label='REJECT', human_evidence='Synthetic fixture only')
    path.unlink(); write_csv(path, columns, rows)
    before = path.read_bytes()
    report, issues = audit_annotations(out)
    assert all(report['checks'].values())
    assert len(issues) == 6 and all(r['issues'] == 'invalid_label_enum' for r in issues)
    assert report['status'] == 'BLOCKED_VALIDATION'
    assert path.read_bytes() == before
    for row in rows:
        row['human_label'] = 'non_laptop'
    path.unlink(); write_csv(path, columns, rows)
    report, issues = audit_annotations(out)
    assert not issues and report['status'] == 'READY_FOR_REVIEWER_DECLARATION'
    rows[0]['review_text'] = 'changed source'
    path.unlink(); write_csv(path, columns, rows)
    report, _ = audit_annotations(out)
    assert not report['checks']['immutable_source_fields']
    assert report['status'] == 'BLOCKED_VALIDATION'


def test_canonical_evaluation_requires_approval_and_preserves_unknown_history(tmp_path):
    args = fixture_pilot(tmp_path)
    out = tmp_path/'canonical_v2'
    prepare_supplemental_qa(*args[:4], out, *args[4:], sample_size=6, seed=7)
    source = out/'review_annotation.csv'
    columns, rows = read_csv(source)
    for row in rows:
        row.update(human_label='REJECT', human_evidence='Synthetic fixture only')
    source.unlink(); write_csv(source, columns, rows)
    canonical = tmp_path/'canonical.csv'
    normalized = [{**r, 'human_label': 'non_laptop'} for r in rows]
    write_csv(canonical, columns, normalized)
    approval = tmp_path/'approval.json'
    data = {'annotations': [{'path': source.as_posix(), 'sha256': sha256_file(source),
        'annotator': 'fixture', 'human_verified': True, 'human_review_status': 'COMPLETED',
        'review_status': 'APPROVED'}], 'canonical_v2': {
        'source': source.as_posix(), 'source_sha256': sha256_file(source),
        'path': canonical.as_posix(), 'sha256': sha256_file(canonical),
        'mapping': {'REJECT': 'non_laptop'}}}
    approval.write_text(json.dumps(data))
    kwargs = dict(annotator='fixture', confirm_human=True, ai_assisted_review=None,
                  review_annotations=canonical, review_confirmation=approval)
    result = evaluate_supplemental_qa(out, **kwargs)
    assert result['label_provenance'] == 'unspecified' and result['human_verified']
    assert result['ai_assistance'] is None
    assert result['counts'] == {'TN': 6}
    assert result['combined_weighted_estimates']['intervals']['recall'][0] < 1
    with pytest.raises(ValueError, match='confirmation'):
        evaluate_supplemental_qa(out, annotator='fixture', confirm_human=True,
                                review_annotations=canonical)
    normalized[0]['human_notes'] = 'unapproved changed note'
    canonical.unlink(); write_csv(canonical, columns, normalized)
    data['canonical_v2']['sha256'] = sha256_file(canonical)
    approval.write_text(json.dumps(data))
    with pytest.raises(ValueError, match='more than'):
        evaluate_supplemental_qa(out, **kwargs)
