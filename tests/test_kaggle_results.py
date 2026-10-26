"""Kiểm verifier với artifacts thật và bản sao bị sửa có chủ đích; không chạy model."""
from pathlib import Path
import shutil
import zipfile
import numpy as np
import pytest
from scripts.verify_kaggle_results import PROJECT_ROOT,read,write,sha,verify_package,compare_metrics,extract_archive

ARTIFACT=PROJECT_ROOT/'artifacts/cloud_runs/tabpfn_full21k_20261024'


def test_real_kaggle_package_and_local_recomputed_metrics():
    result=verify_package(ARTIFACT)
    assert result['integrity_status']=='PASS'
    for slug in ['v3','v35']:
        r=result['models'][slug]
        assert r['status']=='SUCCESS' and r['train_samples']==21000
        assert r['metric_max_abs_delta']=={'validation':0,'test':0}
        assert r['probe_full21k']['sample_count']==21000
    assert result['models']['v3']['checkpoint']!=result['models']['v35']['checkpoint']


def test_metrics_rejects_nan_and_outside_tolerance():
    with pytest.raises(ValueError):compare_metrics({'f1':.5},{'f1':np.nan})
    with pytest.raises(ValueError):compare_metrics({'f1':.5},{'f1':.500001})
    assert compare_metrics({'f1':.5},{'f1':.5+1e-14})<1e-12


@pytest.mark.parametrize('name',['../escape.txt','/absolute.txt','C:/escape.txt','a\\escape.txt'])
def test_archive_rejects_unsafe_members(tmp_path,name):
    archive=tmp_path/'fixture.zip'
    with zipfile.ZipFile(archive,'w') as z:z.writestr(name,'fixture')
    if '\\' in name:
        from scripts.verify_kaggle_results import safe_member
        with pytest.raises(ValueError):safe_member(name)
        return
    with pytest.raises(ValueError):extract_archive(archive,tmp_path/'out')
    assert not (tmp_path/'out').exists()


def test_archive_never_overwrites(tmp_path):
    archive=tmp_path/'fixture.zip'
    with zipfile.ZipFile(archive,'w') as z:z.writestr('fixture.txt','fixture')
    out=tmp_path/'out';extract_archive(archive,out)
    with pytest.raises(FileExistsError):extract_archive(archive,out)


@pytest.mark.parametrize('fault',['train_count','version','predictions','lock','metric','missing','failed'])
def test_tampered_or_incomplete_cloud_is_not_success(tmp_path,fault):
    copied=tmp_path/'copy';shutil.copytree(ARTIFACT,copied)
    folder=copied/'tabpfn_v3_full21k'
    if fault in ['train_count','version','failed']:
        meta=read(folder/'run_metadata.json')
        if fault=='train_count':meta['train_count']=10000
        if fault=='version':meta['resolved_version']='V3_5'
        if fault=='failed':meta['status']='FULL21K_FAILED'
        write(folder/'run_metadata.json',meta)
    elif fault=='predictions':
        p=folder/'test_predictions.csv';s=p.read_text(encoding='utf-8');p.write_text(s.replace(s.splitlines()[1].split(',')[0],'wrong-id',1),encoding='utf-8')
    elif fault=='lock':
        lock=read(folder/'selection_lock.json');lock['train_count']=1500;write(folder/'selection_lock.json',lock)
    elif fault=='metric':
        m=read(folder/'test_metrics.json');m['macro_f1']+=.01;write(folder/'test_metrics.json',m)
    else:(folder/'test_predictions.csv').unlink()
    # Cập nhật hashes để verifier phải kiểm semantic evidence, không chỉ dừng ở byte tampering.
    hashes=read(folder/'hashes.json')
    write(folder/'hashes.json',{n:sha(folder/n) for n in hashes if (folder/n).exists()})
    archive=read(copied/'archive_hashes.json')
    write(copied/'archive_hashes.json',{n:sha(copied/n) for n in archive if (copied/n).exists()})
    result=verify_package(copied)
    assert result['models']['v3']['status']!='SUCCESS'
    if fault=='failed':assert result['models']['v3']['status']=='FULL21K_FAILED'


def test_publish_main_table_preserves_other_models_and_history():
    import pandas as pd
    from scripts.publish_kaggle_results import HISTORY
    old=pd.read_csv(PROJECT_ROOT/HISTORY/'p7_unified_results.csv').set_index('model')
    new=pd.read_csv(PROJECT_ROOT/'reports/p7_unified_results.csv').set_index('model')
    for name in ['E00_majority','E01_xgboost_embedding','E02_tabm_embedding','E05_transformer']:
        for column in old.columns:
            assert old.loc[name,column]==new.loc[name,column] or (pd.isna(old.loc[name,column]) and pd.isna(new.loc[name,column]))
    for name in ['E03_tabpfn_v3_embedding','E04_tabpfn_v35_embedding']:
        assert new.loc[name,'train_samples']==21000 and new.loc[name,'data_regime']=='FULL'
        assert old.loc[name,'data_regime']=='SUBSAMPLED'
