"""Xuất gói đã xác minh từ cache hiện hữu; không tạo embeddings hoặc split."""
from pathlib import Path
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import yaml

ROOT=Path(__file__).resolve().parents[1]
BUNDLE=ROOT/'cloud/kaggle_tabpfn_full21k'
sys.path.insert(0,str(BUNDLE/'scripts'))
from common import sha, write


def main():
    cfg=yaml.safe_load((ROOT/'configs/semantic_benchmark.yaml').read_text(encoding='utf-8'))
    cache=ROOT/cfg['cache']; meta=json.loads((cache/'metadata.json').read_text(encoding='utf-8'))
    if meta['status']!='PASS': raise ValueError('Cache chưa PASS')
    if sha(ROOT/cfg['source'])!=meta['identity']['dataset_hash']: raise ValueError('Dataset hash')
    for name,digest in meta['files_sha256'].items():
        if sha(cache/name)!=digest: raise ValueError('Cache hash: '+name)
    manifest={'project':'customer-sentiment-laptop-reviews','created_at':datetime.now(timezone.utc).isoformat(),
        'seed':42,'dataset_scope':'English laptop-only; rating-derived proxy labels',
        'train_count':21000,'validation_count':4500,'test_count':4500,
        'embedding_model':meta['embedding_model'],'embedding_revision':meta['model_revision'],
        'embedding_dimension':meta['embedding_dimension'],'embedding_dtype':meta['dtype'],
        'embedding_normalized':meta['normalization'],'label_mapping':{'negative':0,'neutral':1,'positive':2},
        'tabpfn_package_version':'9.2.0','expected_versions':{'TabPFN-3':'ModelVersion.V3','TabPFN-3.5':'ModelVersion.V3_5'},
        'source_split_hashes':meta['identity']['split_hash'],'source_embedding_hashes':{},'splits':{},
        'source_cache_metadata_sha256':sha(cache/'metadata.json'),'test_reused':True}
    for split,count in zip(['train','validation','test'],[21000,4500,4500]):
        source=ROOT/cfg['splits']/f'{split}.parquet'
        if sha(source)!=manifest['source_split_hashes'][split]: raise ValueError('Split hash')
        frame=pd.read_parquet(source)
        mapping=pd.read_parquet(cache/f'{split}_mapping.parquet')
        x=np.load(cache/f'{split}_embeddings.npy',mmap_mode='r',allow_pickle=False)
        y=np.load(cache/f'{split}_labels.npy',allow_pickle=False)
        if len(frame)!=count or mapping.review_id.tolist()!=frame.review_id.tolist() or mapping.row_index.tolist()!=list(range(count)) or not np.array_equal(y,frame.label_id.to_numpy()):
            raise ValueError('Alignment FAIL')
        for kind,suffix in [('embeddings','embeddings'),('labels','labels')]:
            shutil.copyfile(cache/f'{split}_{suffix}.npy',BUNDLE/f'data/{kind}/{split}.npy')
        np.save(BUNDLE/f'data/ids/{split}.npy',np.asarray(mapping.review_id.tolist(),dtype=str),allow_pickle=False)
        manifest['source_embedding_hashes'][split]=sha(cache/f'{split}_embeddings.npy')
        manifest['splits'][split]={'shape':list(x.shape),'dtype':str(x.dtype),'byte_size':(cache/f'{split}_embeddings.npy').stat().st_size,
            'alignment_verified':True,'source_mapping_sha256':sha(cache/f'{split}_mapping.parquet'),
            'ordered_ids_sha256':sha(BUNDLE/f'data/ids/{split}.npy')}
    write(BUNDLE/'metadata/label_mapping.json',manifest['label_mapping'])
    # Manifest và anchor tách riêng để tránh hash tự tham chiếu.
    excluded={'metadata/bundle_manifest.json','metadata/hashes.json','config/expected_manifest.json'}
    manifest['bundle_file_hashes']={p.relative_to(BUNDLE).as_posix():sha(p) for p in sorted(BUNDLE.rglob('*'))
        if p.is_file() and p.relative_to(BUNDLE).as_posix() not in excluded and '__pycache__' not in p.parts}
    write(BUNDLE/'metadata/bundle_manifest.json',manifest)
    write(BUNDLE/'metadata/hashes.json',manifest['bundle_file_hashes'])
    write(BUNDLE/'config/expected_manifest.json',{'manifest_sha256':sha(BUNDLE/'metadata/bundle_manifest.json'),
        'counts':dict(zip(['train','validation','test'],[21000,4500,4500]))})
    print('Export PASS: không shuffle/recompute/resplit')

if __name__=='__main__': main()
