"""Nhập và xác minh kết quả Kaggle đã lưu; không import hoặc chạy model."""
import argparse
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import shutil
import stat
import zipfile

import numpy as np
import pandas as pd
import yaml
from src.config import PROJECT_ROOT
from src.evaluation.classification import classification_metrics

VERSIONS = {'v3': ('V3', 'E03_tabpfn_v3_embedding', 'tabpfn-v3-classifier-v3_default.ckpt'),
            'v35': ('V3_5', 'E04_tabpfn_v35_embedding', 'tabpfn-v3.5-20260909.safetensors')}
REQUIRED = {'config.json','environment.json','run_metadata.json','validation_metrics.json','test_metrics.json',
            'validation_predictions.csv','test_predictions.csv','confusion_matrix_validation.csv',
            'confusion_matrix_test.csv','resource_usage.json','hashes.json','run_summary.md','selection_lock.json'}


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write(path,value):
    Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')


def require(condition,message):
    if not condition: raise ValueError(message)


def safe_member(name):
    require('\\' not in name and ':' not in name,'ZIP có đường dẫn không an toàn')
    path=PurePosixPath(name)
    require(not path.is_absolute() and '..' not in path.parts and str(path) not in ('','.','/'),'ZIP path traversal')
    return path


def extract_archive(source,destination):
    """Không overwrite; kiểm toàn bộ member và CRC trước khi giải nén."""
    with zipfile.ZipFile(source) as z:
        require(z.testzip() is None,'ZIP CRC FAIL')
        infos=z.infolist()
        names=[str(safe_member(i.filename)) for i in infos]
        require(len(names)==len(set(names)),'ZIP có member trùng')
        require(sum(i.file_size for i in infos)<100_000_000,'ZIP vượt giới hạn100MB của gói kết quả')
        require(all(not stat.S_ISLNK(i.external_attr>>16) for i in infos),'ZIP chứa symlink')
        destination.mkdir(parents=True,exist_ok=False)
        for i,name in zip(infos,names):
            target=destination/name
            if i.is_dir(): target.mkdir(parents=True,exist_ok=True)
            else:
                target.parent.mkdir(parents=True,exist_ok=True)
                with z.open(i) as src,target.open('xb') as dst:shutil.copyfileobj(src,dst)


def compare_metrics(actual,saved):
    """So toàn bộ cấu trúc bằng abs tolerance1e-12, không bỏ qua NaN."""
    deltas=[]
    def compare(a,b):
        if isinstance(a,dict):
            require(isinstance(b,dict) and set(a)==set(b),'Metric keys khác nhau')
            for k in a: compare(a[k],b[k])
        elif isinstance(a,list):
            require(isinstance(b,list) and len(a)==len(b),'Metric shape khác nhau')
            for x,y in zip(a,b): compare(x,y)
        elif isinstance(a,(float,int)):
            require(isinstance(b,(float,int)) and math.isfinite(b),'Metric không hữu hạn')
            delta=abs(a-b); deltas.append(delta)
            require(delta<=1e-12,'Metric sai lệch ngoài1e-12')
        else:require(a==b,'Metric label/order khác nhau')
    compare(actual,saved)
    return max(deltas,default=0.)


def verify_package(root,project=PROJECT_ROOT):
    root,project=Path(root).resolve(),Path(project).resolve()
    answer={'integrity_status':'INVALID','models':{},'warnings':[
        'Bằng chứng protocol là code bundle được hash, config/selection lock và metadata; không có attestation độc lập hoặc log timestamp fit/test.',
        'Test được tái sử dụng; không suy diễn là holdout mới. Không chạy lại model để xác minh.']}
    for slug in VERSIONS:answer['models'][slug]={'status':'INCOMPLETE'}
    try:
        archive=read(root/'archive_hashes.json')
        expected_files={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and not p.relative_to(root).as_posix().startswith('bundle_metadata/') and p.name!='archive_hashes.json'}
        require(set(archive)==expected_files,'Archive hash coverage thiếu/thừa')
        for name,digest in archive.items():require(sha(root/str(safe_member(name)))==digest,'Archive SHA256 FAIL: '+name)
        bundle=project/'cloud/kaggle_tabpfn_full21k'
        manifest=read(root/'bundle_metadata/bundle_manifest.json')
        require(sha(root/'bundle_metadata/bundle_manifest.json')==sha(bundle/'metadata/bundle_manifest.json'),'Manifest khác bundle local')
        for name in ['hashes.json','label_mapping.json']:
            require(sha(root/'bundle_metadata'/name)==sha(bundle/'metadata'/name),'Metadata khác local: '+name)
        require(manifest['label_mapping']=={'negative':0,'neutral':1,'positive':2},'Sai label mapping')
        require(manifest['embedding_dimension']==384 and manifest['embedding_dtype']=='float32','Sai representation')
        for name,digest in manifest['bundle_file_hashes'].items():require(sha(bundle/str(safe_member(name)))==digest,'Bundle local hash FAIL: '+name)
        cfg=yaml.safe_load((project/'configs/semantic_benchmark.yaml').read_text(encoding='utf-8'))
        source={}
        for split,count in zip(['train','validation','test'],[21000,4500,4500]):
            require(sha(project/cfg['splits']/f'{split}.parquet')==manifest['source_split_hashes'][split],'Split hash FAIL')
            x=np.load(project/cfg['cache']/f'{split}_embeddings.npy',mmap_mode='r',allow_pickle=False)
            require(sha(project/cfg['cache']/f'{split}_embeddings.npy')==manifest['source_embedding_hashes'][split],'Embedding hash FAIL')
            frame=pd.read_parquet(project/cfg['splits']/f'{split}.parquet',columns=['review_id','label_id'])
            ids=np.load(bundle/f'data/ids/{split}.npy',allow_pickle=False)
            labels=np.load(bundle/f'data/labels/{split}.npy',allow_pickle=False)
            require(len(frame)==count and x.shape==(count,384) and x.dtype==np.float32,'Shape/dtype FAIL')
            require(frame.review_id.tolist()==ids.tolist() and np.array_equal(frame.label_id,labels),'Source ID/label alignment FAIL')
            require(frame.review_id.is_unique,'Source ID trùng')
            source[split]=frame
        require(sum(len(set(source[a].review_id)&set(source[b].review_id)) for a,b in [('train','validation'),('train','test'),('validation','test')])==0,'Split ID overlap')
        answer['integrity_status']='PASS'
    except (ValueError,KeyError,FileNotFoundError,TypeError) as exc:
        answer['integrity_error']=str(exc)
        for slug in VERSIONS:answer['models'][slug]={'status':'INVALID','error':str(exc)}
        return answer
    expected_cfg=yaml.safe_load((bundle/'config/cloud_experiment.yaml').read_text(encoding='utf-8'))
    for slug,(version,experiment,checkpoint) in VERSIONS.items():
        result=answer['models'][slug]; folder=root/f'tabpfn_{slug}_full21k'
        try:
            meta=read(folder/'run_metadata.json')
            result.update(train_samples=meta.get('train_count'),requested_version=meta.get('requested_version'),resolved_version=meta.get('resolved_version'))
            if meta.get('status')=='FULL21K_FAILED':
                result.update(status='FULL21K_FAILED',error=meta.get('error',meta.get('reason')),resource=read(folder/'resource_usage.json') if (folder/'resource_usage.json').exists() else None)
                continue
            require(meta['status']=='PASS','Run không PASS')
            require(all((folder/n).is_file() for n in REQUIRED),'INCOMPLETE: thiếu run artifact')
            hashes=read(folder/'hashes.json')
            require(set(hashes)==REQUIRED-{'hashes.json'},'Run hashes coverage FAIL')
            for name,digest in hashes.items():require(sha(folder/str(safe_member(name)))==digest,'Run hash FAIL')
            require(meta['train_count']==21000 and meta['data_regime']=='FULL' and meta['seed']==42,'Không phải full21000/seed42')
            require(meta['experiment']==experiment.replace('E03_tabpfn_v3_embedding','C-E03').replace('E04_tabpfn_v35_embedding','C-E04'),'Sai experiment')
            require(meta['requested_version']==meta['resolved_version']==version and meta['checkpoint']==checkpoint and meta['tabpfn_package_version']=='9.2.0','Version/checkpoint/package FAIL')
            for key in ['source_split_hashes','source_embedding_hashes']:require(meta[key]==manifest[key],key+' FAIL')
            require(meta['bundle_manifest_sha256']==sha(bundle/'metadata/bundle_manifest.json'),'Run manifest hash FAIL')
            env=read(folder/'environment.json');result['environment']=env
            require(env['packages']['tabpfn']=='9.2.0' and env['gpu'] and env['python'] and env['cuda'],'Environment thiếu hoặc sai')
            config=read(folder/'config.json');lock=read(folder/'selection_lock.json')
            require(config==expected_cfg,'Config khác candidate định trước')
            require(lock['settings']==config['model'] and lock['seed']==42 and lock['train_count']==21000,'Lock config/train FAIL')
            require(lock['resolution']=={k:meta[k] for k in ['requested_version','resolved_version','checkpoint','tabpfn_package_version']},'Lock resolution FAIL')
            require(meta['selection_lock_sha256']==sha(folder/'selection_lock.json') and lock['validation_metrics_sha256']==sha(folder/'validation_metrics.json'),'Lock hash FAIL')
            require(config['protocol']['test_reused'] is True and meta['test_reused'] is True and config['protocol']['resource_probe']=='train_only' and config['protocol']['selection']=='single_predeclared_configuration','Protocol FAIL')
            probe=read(root/f'resource_probe_{slug}.json')
            require(probe['status']=='PASS' and probe['train_only'] is True,'Probe FAIL')
            require([r['sample_count'] for r in probe['results']]==[500,1000,2500,5000,10000,21000],'Probe không đủ full21K')
            for row in probe['results']:
                require(row['status']=='PASS' and row['split']=='train' and row['feature_dimension']==384 and row['dtype']=='float32','Probe data FAIL')
                require(row['requested_version']==row['resolved_version']==version and row['checkpoint']==checkpoint and row['tabpfn_package_version']=='9.2.0','Probe version FAIL')
            result['metrics']={};result['metric_max_abs_delta']={}
            for split in ['validation','test']:
                predictions=pd.read_csv(folder/f'{split}_predictions.csv',dtype={'review_id':str})
                require({'review_id','y_true','y_pred'}<=set(predictions),'Prediction schema FAIL')
                require(predictions.review_id.tolist()==source[split].review_id.tolist(),'Prediction IDs/order FAIL')
                require(np.array_equal(predictions.y_true,source[split].label_id),'Prediction y_true FAIL')
                require(predictions.y_pred.dtype.kind in 'iu' and predictions.y_pred.isin([0,1,2]).all(),'Prediction labels FAIL')
                metrics=classification_metrics(predictions.y_true,predictions.y_pred)
                metrics['balanced_accuracy']=float(np.mean([r['recall'] for r in metrics['per_class'].values()]))
                metrics['neutral_f1']=metrics['per_class']['neutral']['f1']
                result['metric_max_abs_delta'][split]=compare_metrics(metrics,read(folder/f'{split}_metrics.json'))
                cm=pd.read_csv(folder/f'confusion_matrix_{split}.csv',index_col=0)
                require(list(cm.index)==list(cm.columns)==['negative','neutral','positive'] and np.array_equal(cm.to_numpy(),metrics['confusion_matrix']),'Confusion CSV FAIL')
                result['metrics'][split]=metrics
            resource=read(folder/'resource_usage.json');result['resource']=resource
            for key in ['fit_seconds','validation_inference_seconds','test_inference_seconds','wall_seconds','peak_process_rss_bytes','peak_gpu_allocated_bytes','peak_gpu_reserved_bytes']:
                require(isinstance(resource[key],(int,float)) and math.isfinite(resource[key]) and resource[key]>0,'Resource thiếu/không hợp lệ')
            require(resource['peak_gpu_allocated_bytes']<=resource['peak_gpu_reserved_bytes'],'GPU memory FAIL')
            result.update(status='SUCCESS',checkpoint=checkpoint,artifact_directory=folder.relative_to(project).as_posix(),probe_full21k=probe['results'][-1],protocol_status='PASS_WITH_EVIDENCE_LIMITATIONS')
        except FileNotFoundError as exc:result.update(status='INCOMPLETE',error=str(exc))
        except (ValueError,KeyError,TypeError) as exc:result.update(status='INCOMPLETE' if str(exc).startswith('INCOMPLETE:') else 'INVALID',error=str(exc))
    return answer


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('zip',type=Path);p.add_argument('--destination',type=Path,required=True)
    a=p.parse_args();extract_archive(a.zip,a.destination)
    result=verify_package(a.destination)
    result.update(zip_source=a.zip.as_posix(),zip_sha256=sha(a.zip),artifact_directory=a.destination.as_posix(),tests='PENDING')
    write(PROJECT_ROOT/'reports/tabpfn_kaggle_full21k_verification.json',result)
    print(json.dumps({k: v['status'] for k,v in result['models'].items()}))

if __name__=='__main__':main()
