"""Fixtures tổng hợp chỉ kiểm giao thức gói; không phải kết quả benchmark."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import types
import numpy as np
import pytest

BUNDLE=Path(__file__).resolve().parents[1]/'cloud/kaggle_tabpfn_full21k'
sys.path.insert(0,str(BUNDLE/'scripts'))
import common
import run_tabpfn_cloud as runner


def test_actual_bundle_integrity():
    data,m=common.verify(BUNDLE)
    assert [len(data[s][1]) for s in common.SPLITS]==[21000,4500,4500]
    assert m['embedding_dimension']==384
    assert m['expected_versions']=={'TabPFN-3':'ModelVersion.V3','TabPFN-3.5':'ModelVersion.V3_5'}


@pytest.fixture
def fixture_bundle(tmp_path,monkeypatch):
    monkeypatch.setattr(common,'COUNTS',(6,6,6))
    for d in ['metadata','config','data/embeddings','data/labels','data/ids']:(tmp_path/d).mkdir(parents=True,exist_ok=True)
    for split in common.SPLITS:
        np.save(tmp_path/f'data/embeddings/{split}.npy',np.ones((6,4),dtype='float32'))
        np.save(tmp_path/f'data/labels/{split}.npy',np.array([0,1,2,0,1,2]))
        np.save(tmp_path/f'data/ids/{split}.npy',np.array([f'{split}-{i}' for i in range(6)]))
    common.write(tmp_path/'metadata/label_mapping.json',common.LABELS)
    def anchor():
        m={'label_mapping':common.LABELS,'embedding_dimension':4,'embedding_dtype':'float32',
           'splits':{s:{'alignment_verified':True} for s in common.SPLITS},
           'bundle_file_hashes':{p.relative_to(tmp_path).as_posix():common.sha(p) for p in tmp_path.rglob('*.npy')}}
        common.write(tmp_path/'metadata/hashes.json',m['bundle_file_hashes'])
        common.write(tmp_path/'metadata/bundle_manifest.json',m)
        common.write(tmp_path/'config/expected_manifest.json',{'manifest_sha256':common.sha(tmp_path/'metadata/bundle_manifest.json')})
    anchor()
    return tmp_path,anchor


@pytest.mark.parametrize('fault',['count','nan','inf','zero','dtype','labels','overlap','duplicate','mapping','anchor','hash'])
def test_reject_invalid_bundle(fixture_bundle,fault):
    root,anchor=fixture_bundle
    xp=root/'data/embeddings/train.npy'; yp=root/'data/labels/train.npy'; ip=root/'data/ids/train.npy'
    if fault in ['nan','inf','zero','dtype','count']:
        x=np.load(xp)
        if fault=='nan':x[0,0]=np.nan
        if fault=='inf':x[0,0]=np.inf
        if fault=='zero':x[:]=0
        if fault=='dtype':x=x.astype('float64')
        if fault=='count':x=x[:-1]
        np.save(xp,x)
    if fault=='labels':np.save(yp,np.zeros(6,dtype='int64'))
    if fault=='overlap':np.save(ip,np.load(root/'data/ids/test.npy'))
    if fault=='duplicate':np.save(ip,np.array(['a']*6))
    if fault=='mapping':common.write(root/'metadata/label_mapping.json',{'positive':0})
    if fault=='hash':np.save(xp,np.zeros((6,4),dtype='float32'))
    else:anchor()
    if fault=='anchor':common.write(root/'metadata/bundle_manifest.json',{})
    with pytest.raises(ValueError):common.verify(root)


@pytest.mark.parametrize('secret',['TABPFN_TOKEN=fixture_secret_1234567890','Bearer fixture_secret_1234567890','hf_'+'z'*25,'sk-'+'z'*25])
def test_secret_scan_rejects(tmp_path,secret):
    (tmp_path/'leak.txt').write_text(secret)
    with pytest.raises(ValueError):common.secret_scan(tmp_path)


@pytest.mark.parametrize('script',['verify_bundle.py','run_tabpfn_cloud.py','resource_probe.py','package_results.py'])
def test_cli_help_standalone(script,tmp_path):
    result=subprocess.run([sys.executable,str(BUNDLE/'scripts'/script),'--help'],cwd=tmp_path,capture_output=True)
    assert result.returncode==0


def test_explicit_versions_and_protocol():
    source=(BUNDLE/'scripts/versions.py').read_text(encoding='utf-8')
    assert "'V3'" in source and "'V3_5'" in source
    assert 'create_default_for_version' in source
    assert 'TabPFNClassifier()' not in source
    source=(BUNDLE/'scripts/run_tabpfn_cloud.py').read_text(encoding='utf-8-sig')
    assert source.index("'validation',batch")<source.index("write(out/'selection_lock.json'")<source.index("'test',batch")
    for p in (BUNDLE/'scripts').glob('*.py'):
        assert not any(s in p.read_text(encoding='utf-8-sig').lower() for s in ['tfidf','tf-idf','truncatedsvd','pca('])


def test_fixture_run_output_schema_and_lock(tmp_path,monkeypatch):
    values=(np.ones((6,4),dtype='float32'),np.array([0,1,2,0,1,2]),np.array([f'fixture-{i}' for i in range(6)]))
    data={s:values for s in common.SPLITS}
    manifest={'source_split_hashes':{},'source_embedding_hashes':{}}
    monkeypatch.setattr(runner,'verify',lambda _: (data,manifest))
    monkeypatch.setattr(runner,'environment',lambda: {'fixture':True})
    monkeypatch.setattr(runner,'cleanup',lambda:None)
    fake_cuda=types.SimpleNamespace(synchronize=lambda:None,reset_peak_memory_stats=lambda:None,max_memory_allocated=lambda:0,max_memory_reserved=lambda:0)
    monkeypatch.setitem(sys.modules,'torch',types.SimpleNamespace(cuda=fake_cuda,manual_seed=lambda _:None,set_num_threads=lambda _:None))
    out=tmp_path/'fixture_output'
    class FixtureModel:
        calls=0
        def fit(self,x,y):assert len(y)==6
        def predict(self,x):
            self.calls+=1
            if self.calls==2:assert (out/'selection_lock.json').exists()
            return np.array([0,1,2,0,1,2])[:len(x)]
    monkeypatch.setattr(runner,'model_for',lambda v,c:(FixtureModel(),{'requested_version':'V3','resolved_version':'V3','checkpoint':'fixture'}))
    args=types.SimpleNamespace(data_root=BUNDLE,output_dir=out,version='v3')
    assert runner.run(args)==0
    assert common.load(out/'run_metadata.json')['status']=='PASS'
    assert set(common.load(out/'test_metrics.json')['per_class'])==set(common.LABELS)
    assert (out/'test_predictions.csv').read_text().splitlines()[0]=='review_id,y_true,y_pred'
    assert common.load(out/'hashes.json')['selection_lock.json']==common.sha(out/'selection_lock.json')
    with pytest.raises(FileExistsError):runner.run(args)


def test_metrics_reused_byte_exact():
    assert (BUNDLE/'scripts/metrics.py').read_bytes()==(BUNDLE.parents[1]/'src/evaluation/classification.py').read_bytes()


def test_notebook_cells_compile_and_no_outputs():
    notebook=common.load(BUNDLE/'kaggle_notebook.ipynb')
    codes=[c for c in notebook['cells'] if c['cell_type']=='code']
    assert len(codes)==11
    for c in codes:
        assert c['outputs']==[] and c['execution_count'] is None
        compile(''.join(c['source']),'<fixture-notebook>','exec')


def test_package_allowlist_and_failure_artifacts(tmp_path):
    from package_results import package
    import zipfile
    out=tmp_path/'tabpfn_v3_full21k';out.mkdir()
    common.write(out/'run_metadata.json',{'status':'FULL21K_FAILED'})
    common.write(out/'hashes.json',{'run_metadata.json':common.sha(out/'run_metadata.json')})
    (out/'weights.bin').write_bytes(b'fixture not a model')
    (tmp_path/'unrelated.txt').write_text('excluded')
    archive=package(tmp_path,BUNDLE)
    with zipfile.ZipFile(archive) as z:
        assert 'tabpfn_v3_full21k/run_metadata.json' in z.namelist()
        assert not any('weights' in n or 'unrelated' in n for n in z.namelist())
        assert 'bundle_metadata/bundle_manifest.json' in z.namelist()
        assert 'archive_hashes.json' in z.namelist()


def test_package_rejects_incomplete_pass(tmp_path):
    from package_results import package
    out=tmp_path/'tabpfn_v3_full21k';out.mkdir()
    common.write(out/'run_metadata.json',{'status':'PASS'})
    with pytest.raises(ValueError):package(tmp_path,BUNDLE)


def test_probe_failure_skips_final_without_subsample(tmp_path,monkeypatch):
    from notebook_steps import full_after_probe
    common.write(tmp_path/'resource_probe_v3.json',{'status':'FULL21K_FAILED'})
    monkeypatch.setattr(subprocess,'run',lambda *a,**k:pytest.fail('Không được chạy final khi probe FAIL'))
    full_after_probe(BUNDLE,tmp_path,'v3')
    m=common.load(tmp_path/'tabpfn_v3_full21k/run_metadata.json')
    assert m['status']=='FULL21K_FAILED' and m['test_evaluated'] is False
