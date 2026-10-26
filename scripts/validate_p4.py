"""Xác minh tải lại chỉ đọc của tư cách thành viên cố định P4 và tiền xử lý các tệp kết quả."""

import argparse
import io
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from scipy import sparse

from src.config import PROJECT_ROOT
from src.data.acquisition import sha256_file
from src.data.p2_pipeline import load_qa_guards
from src.data.split import SPLITS, assign_splits, validate_splits
from src.preprocessing.bert import BertPreprocessor
from src.preprocessing.english import ordered_id_digest


def validate(root: Path, run: Path, output: Path) -> dict:
    """Xác minh đầu ra đã cố định mà không lắp hoặc thay đổi bất kỳ dataset/manifest. nào"""
    run,output=run.resolve(),output.resolve()
    if not run.is_relative_to((root/'reports/p4').resolve()) or not output.is_relative_to(run):
        raise ValueError('P4 validation output must be inside requested report run')
    if output.exists():raise FileExistsError('Use a new validation path')
    manifest=json.loads((run/'manifest.json').read_text(encoding='utf-8'))
    for rel,digest in manifest['output_sha256'].items():
        if sha256_file(root/rel)!=digest:raise ValueError(f'Artifact changed: {rel}')
    for rel,digest in manifest['implementation_sha256'].items():
        if sha256_file(root/rel)!=digest:raise ValueError(f'Implementation changed: {rel}')
    snapshot=json.loads((run/'input_preservation.json').read_text(encoding='utf-8'))
    for rel,digest in snapshot.items():
        if sha256_file(root/rel)!=digest:raise ValueError(f'Previously completed input changed: {rel}')
    cfg=manifest['configuration']
    source=pd.read_parquet(root/manifest['source'])
    if sha256_file(root/manifest['source'])!=manifest['source_sha256']:raise ValueError('Source changed')
    splits_dir=root/manifest['paths']['splits'];pre_dir=root/manifest['paths']['preprocessing']
    features_dir=root/manifest['paths']['features']
    frames={name:pd.read_parquet(splits_dir/f'{name}.parquet') for name in SPLITS}
    assigned=pd.concat(frames.values(),ignore_index=True)
    excluded=set(pd.read_csv(run/'exclusions.csv',keep_default_na=False).review_id)
    p2=json.loads((root/cfg['p2_manifest']).read_text(encoding='utf-8'))
    qa_ids,qa_keys=load_qa_guards([root/p for p in p2['qa_sources']])
    noise=pd.read_parquet(root/'data/interim/p2/20261009_final/label_noise_candidates.parquet')
    pairs=json.loads((run/'near_pairs.json').read_text(encoding='utf-8'))
    validation=validate_splits(source,assigned,qa_ids=qa_ids,qa_keys=qa_keys,noise=noise,
                               near_pairs=pairs,excluded_ids=excluded)
    strategy=manifest['strategy']
    replay,_=assign_splits(source[~source.review_id.isin(excluded)].iloc[::-1],seed=strategy['seed'],
                           ratios=[strategy['ratios'][name] for name in SPLITS],near_pairs=pairs)
    byte_replay={}
    for name in SPLITS:
        replay_frame=replay[replay.split.eq(name)].reset_index(drop=True)
        buffer=io.BytesIO();replay_frame.to_parquet(buffer,index=False,compression='zstd')
        from hashlib import sha256
        byte_replay[name]=sha256(buffer.getvalue()).hexdigest()==manifest['split_sha256'][name]
    if not all(byte_replay.values()):raise ValueError('Byte-level split replay mismatch')
    classical=joblib.load(pre_dir/'tfidf.joblib')
    preprocessing=json.loads((pre_dir/'preprocessing.json').read_text(encoding='utf-8'))
    if classical.fit_id_sha256!=ordered_id_digest(frames['train'].review_id.tolist()):raise ValueError('Wrong fit IDs')
    if preprocessing['feature_allowlist']!=['text']:raise ValueError('Unexpected features')
    matrix_checks={}
    for name in SPLITS:
        matrix=sparse.load_npz(pre_dir/f'{name}_tfidf.npz')
        transformed=classical.transform(frames[name])
        if (transformed!=matrix).nnz:raise ValueError('Frozen TF-IDF differs from saved matrix')
        ids=pd.read_parquet(pre_dir/f'{name}_feature_rows.parquet')
        pd.testing.assert_frame_equal(ids,frames[name][['review_id','label_id','split']])
        matrix_checks[name]={'rows':matrix.shape[0],'features':matrix.shape[1],'nnz':int(matrix.nnz),'reload':'PASS'}
        if name=='train':
            document_frequency=np.asarray((matrix>0).sum(axis=0)).ravel()
            expected_idf=np.log((1+matrix.shape[0])/(1+document_frequency))+1
            if not np.allclose(expected_idf,classical.vectorizer.idf_,rtol=1e-6,atol=1e-6):
                raise ValueError('IDF is inconsistent with training document frequencies')
            if not (document_frequency>=cfg['tfidf_min_df']).all():raise ValueError('Training min_df violated')
    max_length=preprocessing['bert']['max_length_policy']['max_length']
    bert=BertPreprocessor(pre_dir/'bert/tokenizer.json',max_length=max_length)
    token_checks={}
    for name,frame in frames.items():
        saved=pq.ParquetFile(features_dir/f'{name}_bert.parquet')
        offset=0
        for batch in saved.iter_batches(batch_size=128):
            records=batch.to_pylist();chunk=frame.iloc[offset:offset+len(records)]
            expected=bert.encode(chunk)
            for record,(rid,label),tokens in zip(records,zip(chunk.review_id,chunk.label_id),expected):
                if record['review_id']!=rid or record['label_id']!=label or record['split']!=name:
                    raise ValueError('BERT row alignment mismatch')
                if {k:record[k] for k in tokens}!=tokens:raise ValueError('BERT saved token arrays differ')
                if not all(record['attention_mask']) or any(record['token_type_ids']):raise ValueError('Single-context no-padding contract')
            offset+=len(records)
        if offset!=len(frame):raise ValueError('Missing BERT feature records')
        token_checks[name]={'rows':offset,'all_records_reencoded':'PASS'}
    result={'status':'PASS','schema_and_membership':validation,'split_byte_replay':byte_replay,
            'full_tfidf_retransform':matrix_checks,'idf_train_document_frequency':'PASS',
            'full_bert_reencode':token_checks,'completed_input_checksums':len(snapshot),'protected41':'PASS',
            'features':['text'],'classifiers_trained':False,'no_test_parameter_selection':True}
    output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    return result


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,default=PROJECT_ROOT/'reports/p4/p4_20261009_final')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    output=args.output or args.run/'reload_validation.json'
    result=validate(PROJECT_ROOT,args.run,output)
    print(json.dumps({k:result[k] for k in ('status','split_byte_replay','idf_train_document_frequency','protected41')},indent=2))


if __name__=='__main__':main()
