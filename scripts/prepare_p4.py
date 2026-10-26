"""Tiền xử lý P4 cố định Amazon các tập đã chia và chỉ trên tập huấn luyện; không có trình phân loại hoặc chỉnh sửa SemEval."""

import argparse
import csv
import gc
import json
from pathlib import Path
import re
import time
import urllib.request

import joblib
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from scipy import sparse
import yaml

from src.config import PROJECT_ROOT, load_config
from src.data.acquisition import sha256_file
from src.data.feasibility import check_memory, process_memory
from src.data.near_duplicates import audit_near_duplicates
from src.data.p2_pipeline import load_qa_guards
from src.data.split import SPLITS, LABELS, assign_splits, content_key, validate_splits
from src.preprocessing.english import VERSION, ClassicalPreprocessor, classical_text, minimal_text, ordered_id_digest
from src.preprocessing.bert import BertPreprocessor, choose_max_length


def write_json(path: Path, value: dict | list) -> None:
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def input_snapshot(root: Path, cfg: dict) -> dict[str,str]:
    """Liên kết protected41 cộng với QA/raw nhãn gán và hoàn thành P2/P3 các tệp kết quả."""
    protected=json.loads((root/'reports/tables/p1_recall_brand_preservation.json').read_text(encoding='utf-8'))['files']
    current={p:sha256_file(root/p) for p in protected}
    if current!=protected:raise ValueError('Protected41 bytes differ')
    for directory in ('data/manual','data/interim/semeval','data/interim/annotation_normalization',
                      'reports/p3/20261009_verified','reports/tables/p2_amazon_20261009_final'):
        for p in sorted((root/directory).rglob('*')):
            if p.is_file():current[p.relative_to(root).as_posix()]=sha256_file(p)
    for rel in (cfg['source'],cfg['p2_manifest'],cfg['p3_summary'],
                'reports/p2_amazon_completion_20261009.md','reports/p3_data_analysis_20261009.md',
                'reports/p3_insight_summary_20261009.md','notebooks/03_laptop_eda.ipynb',
                'reports/tables/p1_semeval_owner_exception_20261009.json',
                'data/interim/p2/20261009_final/label_noise_candidates.parquet'):
        current[rel]=sha256_file(root/rel)
    return current


def holdout_rows(root: Path, p2: dict, noise: pd.DataFrame) -> tuple[list[dict],set[str],set[str]]:
    """Chỉ texts/IDs/products dành cho thiết bị bảo vệ chống ô nhiễm; không sử dụng con người nhãn."""
    rows=[];ids=set();products=set()
    for relative,digest in p2['qa_sources'].items():
        path=root/relative
        if sha256_file(path)!=digest:raise ValueError('QA provenance changed')
        with path.open(encoding='utf-8-sig',newline='') as handle:
            for i,row in enumerate(csv.DictReader(handle)):
                ids.add(row.get('review_id') or '')
                products.add(row.get('product_id') or row.get('parent_asin') or '')
                text=row.get('review_text')
                if text and text.strip():
                    rows.append({'review_id':f'holdout:qa:{content_key(relative)}:{i}',
                                 'text':minimal_text(text),'sentiment':'holdout'})
    for _,row in noise.iterrows():
        rows.append({'review_id':f'holdout:noise:{row.review_id}',
                     'text':minimal_text(row.text),'sentiment':'holdout'})
    gold=root/'data/manual/amazon_laptop_gold_test.csv'
    if gold.exists():
        for i,row in pd.read_csv(gold,keep_default_na=False).iterrows():
            text=row.get('review_text') or row.get('text')
            if not isinstance(text,str) or not text.strip():raise ValueError('Invalid existing gold text')
            ids.add(row.get('review_id',''))
            rows.append({'review_id':f'holdout:gold:{i}','text':minimal_text(text),'sentiment':'holdout'})
    return rows,ids-{''},products-{''}


def reserve_holdout_matches(source: pd.DataFrame, holds: list[dict], ids: set[str],
                            pairs: list[dict]) -> dict[str,str]:
    """Chỉ loại trừ tư cách thành viên phân chia phái sinh; bảo quản P2 bytes/labels và ghi lại lý do."""
    source_ids=set(source.review_id)
    normalized={content_key(r['text'].casefold()) for r in holds}
    classical={content_key(classical_text(r['text'])) for r in holds}
    excluded={}
    for _,row in source.iterrows():
        if row.review_id in ids:excluded[row.review_id]='holdout_id'
        elif content_key(row.text.casefold()) in normalized:excluded[row.review_id]='holdout_clean_text'
        elif content_key(classical_text(row.text)) in classical:excluded[row.review_id]='holdout_classical_text'
    reserved=set(excluded)|{r['review_id'] for r in holds}
    # Tuyên truyền các mối quan hệ gần một cách bắc cầu, không chỉ các kết quả phù hợp trực tiếp.
    changed=True
    while changed:
        changed=False
        for pair in pairs:
            a,b=pair['review_id_a'],pair['review_id_b']
            if (a in reserved)!=(b in reserved):
                other=b if a in reserved else a;reserved.add(other);changed=True
                if other in source_ids:excluded[other]='holdout_near_cluster'
    return excluded


def download_tokenizer(cfg: dict, output: Path) -> dict:
    """Chỉ tìm nạp bản sửa đổi cố định tokenizer/config, không bao giờ lấy trọng số hoặc tập dữ liệu mô hình."""
    if not re.fullmatch(r'[0-9a-f]{40}',cfg['bert_revision']):raise ValueError('Immutable BERT revision required')
    if cfg['bert_repo']!='google-bert/bert-base-uncased':raise ValueError('Unexpected tokenizer source')
    result={}
    for name in ('tokenizer.json','config.json'):
        url=f"https://huggingface.co/{cfg['bert_repo']}/resolve/{cfg['bert_revision']}/{name}"
        with urllib.request.urlopen(url,timeout=30) as response:
            data=response.read(5_000_001)
        if len(data)>5_000_000:raise ValueError('Tokenizer resource unexpectedly large')
        json.loads(data)
        target=output/('tokenizer_original.json' if name=='tokenizer.json' else name)
        target.write_bytes(data)
        result[name]={'url':url,'sha256':sha256_file(target),'bytes':len(data)}
    return result


def prepare(root: Path, cfg_path: Path) -> dict:
    """Chỉ thực thi P4 theo thứ tự phụ thuộc, sau đó xác minh reload/replay và bảo quản."""
    cfg=yaml.safe_load(cfg_path.read_text(encoding='utf-8'))
    if not re.fullmatch(r'[A-Za-z0-9_-]+',cfg['output_suffix']):raise ValueError('Invalid output suffix')
    data_cfg=load_config('data',root)
    ratios=[data_cfg['split'][s] for s in SPLITS];seed=data_cfg['seed']
    if ratios!=[.70,.15,.15]:raise ValueError('Official split contract changed')
    source_path=(root/cfg['source']).resolve()
    if not source_path.is_relative_to((root/'data/processed').resolve()):raise ValueError('Unexpected source location')
    paths={'splits':root/'data/processed/splits'/cfg['output_suffix'],
           'features':root/'data/processed/features'/cfg['output_suffix'],
           'preprocessing':root/'artifacts/preprocessing'/cfg['output_suffix'],
           'report':root/'reports/p4'/cfg['output_suffix']}
    for p in paths.values():
        if p.exists():raise FileExistsError(f'Refuse to overwrite {p}')
        if not p.resolve().is_relative_to(root.resolve()):raise ValueError('Output escapes project')
    if sha256_file(source_path)!=cfg['source_sha256']:raise ValueError('Expected P2 dataset changed')
    started=time.monotonic()
    print('P4: binding protected and completed inputs',flush=True)
    snapshot=input_snapshot(root,cfg)
    p2=json.loads((root/cfg['p2_manifest']).read_text(encoding='utf-8'))
    if p2['clean_parquet_sha256']!=cfg['source_sha256']:raise ValueError('P2 manifest mismatch')
    for path in paths.values():path.mkdir(parents=True)
    def guard():
        check_memory(cfg['max_memory_bytes'])
        if time.monotonic()-started>cfg['max_seconds']:raise RuntimeError('P4 time ceiling')
        total=sum(p.stat().st_size for directory in paths.values() for p in directory.rglob('*') if p.is_file())
        if total>cfg['max_output_bytes']:raise RuntimeError('P4 output ceiling')
    source=pd.read_parquet(source_path)
    source_columns=list(source.columns)
    noise=pd.read_parquet(root/'data/interim/p2/20261009_final/label_noise_candidates.parquet')
    holds,holdout_ids,qa_products=holdout_rows(root,p2,noise)
    qa_ids,qa_keys=load_qa_guards([root/p for p in p2['qa_sources']])
    print(f'P4: scoped near-leakage audit, {len(source)} source and {len(holds)} holdout texts',flush=True)
    audit_rows=source[['review_id','text','sentiment']].to_dict('records')+holds
    pairs,near=audit_near_duplicates(audit_rows,seed=seed,threshold=cfg['near_jaccard'],max_comparisons=cfg['max_near_comparisons'])
    del audit_rows
    if near['comparison_cap_reached']:raise ValueError('Near audit capped; review required')
    excluded=reserve_holdout_matches(source,holds,holdout_ids,pairs)
    eligible=source[~source.review_id.isin(excluded)].copy()
    assigned,strategy=assign_splits(eligible,seed=seed,ratios=ratios,near_pairs=pairs)
    validation=validate_splits(source,assigned,qa_ids=qa_ids|holdout_ids,qa_keys=qa_keys,
                               noise=noise,near_pairs=pairs,excluded_ids=set(excluded))
    print('P4: product-isolated splits',json.dumps(validation['counts']),flush=True)
    # Phát lại với thứ tự đầu vào bị đảo ngược: việc gán không được phụ thuộc vào thứ tự đầu vào.
    replay,replay_strategy=assign_splits(eligible.iloc[::-1],seed=seed,ratios=ratios,near_pairs=pairs)
    if strategy!=replay_strategy:raise ValueError('Strategy replay differs')
    pd.testing.assert_frame_equal(assigned[['review_id','split_group_id','split']],replay[['review_id','split_group_id','split']])
    split_hashes={};frames={}
    for name in SPLITS:
        frame=assigned[assigned.split.eq(name)].reset_index(drop=True)
        path=paths['splits']/f'{name}.parquet';frame.to_parquet(path,index=False,compression='zstd')
        frames[name]=pd.read_parquet(path)
        pd.testing.assert_frame_equal(frame,frames[name])
        split_hashes[name]=sha256_file(path)
    assignments=assigned[['review_id','parent_asin','asin','sentiment','label_id','split_group_id','split']]
    assignments.to_csv(paths['report']/'assignments.csv',index=False)
    pd.DataFrame([{'review_id':key,'reason':value} for key,value in sorted(excluded.items())],
                 columns=['review_id','reason']).to_csv(paths['report']/'exclusions.csv',index=False)
    write_json(paths['report']/'near_pairs.json',pairs)
    near.update(source_rows=len(source),holdout_texts=len(holds),
                reused_p2_near_pairs=p2['near_duplicates']['pairs'],new_scope='cross-split and QA/noise holdout control')
    validation.update(near_audit=near,reproducibility='PASS; reversed input order gives identical assignments',
                      qa_product_overlap_diagnostic={s:len(set(f.parent_asin)&qa_products) for s,f in frames.items()},
                      qa_products_policy='P1 domain QA products may overlap; no QA labels used as sentiment labels',
                      label_provenance='rating-derived proxy',source_immutable=True)
    # Bộ dữ liệu kiểm toán đầy đủ đã có persisted/verified; đặc trưng chỉ hoạt động cần text/targets.
    frames={name:frame[['review_id','text','label_id','split','language']].copy() for name,frame in frames.items()}
    del source,noise,holds,eligible,assigned,replay,assignments,frame
    gc.collect()
    guard()
    print('P4: fitting TF-IDF on train review text only',flush=True)
    classical=ClassicalPreprocessor(min_df=cfg['tfidf_min_df'],max_features=cfg['tfidf_max_features'])
    train_matrix=classical.fit_train(frames['train'])
    joblib.dump(classical,paths['preprocessing']/'tfidf.joblib',compress=3)
    restored=joblib.load(paths['preprocessing']/'tfidf.joblib')
    classical_info={'fit_split':'train','fit_rows':classical.fit_rows,'fit_id_sha256':classical.fit_id_sha256,
                    'vocabulary_size':len(classical.vectorizer.vocabulary_),'ngram_range':[1,2],
                    'stopword_removal':False,'stemming':False,'lowercase':True,'punctuation_tokens':True,
                    'min_df':cfg['tfidf_min_df'],'max_features':cfg['tfidf_max_features'],'matrix':{}}
    for name,frame in frames.items():
        matrix=train_matrix if name=='train' else classical.transform(frame)
        sparse.save_npz(paths['preprocessing']/f'{name}_tfidf.npz',matrix)
        frame[['review_id','label_id','split']].to_parquet(paths['preprocessing']/f'{name}_feature_rows.parquet',index=False)
        loaded=sparse.load_npz(paths['preprocessing']/f'{name}_tfidf.npz')
        if (loaded!=matrix).nnz:raise ValueError('Sparse reload mismatch')
        sample=frame.head(8);expected=matrix[:len(sample)]
        if (restored.transform(sample)!=expected).nnz:raise ValueError('TF-IDF reload mismatch')
        classical_info['matrix'][name]={'shape':list(matrix.shape),'nnz':int(matrix.nnz),'dtype':str(matrix.dtype)}
        guard()
    if ordered_id_digest(frames['train'].review_id.tolist())!=classical.fit_id_sha256:raise ValueError('Wrong TF-IDF fit IDs')
    del train_matrix,matrix,loaded,restored,classical,sample,expected
    gc.collect()
    bert_dir=paths['preprocessing']/'bert';bert_dir.mkdir()
    print('P4: acquiring fixed pretrained tokenizer only; choosing length from train',flush=True)
    resources=download_tokenizer(cfg,bert_dir)
    model_config=json.loads((bert_dir/'config.json').read_text(encoding='utf-8'))
    if model_config['max_position_embeddings']!=512:raise ValueError('Unexpected BERT context')
    base=BertPreprocessor(bert_dir/'tokenizer_original.json')
    train_lengths=base.lengths(frames['train'])
    max_length,length_policy=choose_max_length(train_lengths,quantile=cfg['length_quantile'],
                                            candidates=tuple(cfg['length_candidates']))
    bert=BertPreprocessor(bert_dir/'tokenizer_original.json',max_length=max_length)
    bert.tokenizer.save(str(bert_dir/'tokenizer.json'))
    restored_bert=BertPreprocessor(bert_dir/'tokenizer.json',max_length=max_length)
    token_stats={}
    for name,frame in frames.items():
        lengths=train_lengths if name=='train' else base.lengths(frame)
        path=paths['features']/f'{name}_bert.parquet'
        schema=pa.schema([('review_id',pa.string()),('label_id',pa.int64()),('split',pa.string()),
                          ('input_ids',pa.list_(pa.int32())),('attention_mask',pa.list_(pa.int8())),
                          ('token_type_ids',pa.list_(pa.int8()))])
        unknown,total=0,0
        with pq.ParquetWriter(path,schema,compression='zstd') as writer:
            for offset in range(0,len(frame),cfg['batch_size']):
                batch=frame.iloc[offset:offset+cfg['batch_size']]
                encodings=bert.encode(batch)
                records=[]
                for (rid,label_id),encoding in zip(zip(batch.review_id,batch.label_id),encodings):
                    ids=encoding['input_ids'];total+=len(ids);unknown+=ids.count(bert.tokenizer.token_to_id('[UNK]'))
                    if not 2<=len(ids)<=max_length or ids[0]!=101 or ids[-1]!=102:raise ValueError('BERT sequence contract')
                    if not (len(ids)==len(encoding['attention_mask'])==len(encoding['token_type_ids'])):raise ValueError('BERT lengths differ')
                    records.append({'review_id':rid,'label_id':int(label_id),'split':name,**encoding})
                writer.write_table(pa.Table.from_pylist(records,schema=schema));guard()
        table=pq.read_table(path,columns=['review_id','label_id'])
        if table.column('review_id').to_pylist()!=frame.review_id.tolist():raise ValueError('Feature row alignment')
        if table.column('label_id').to_pylist()!=frame.label_id.tolist():raise ValueError('Feature label alignment')
        sample=frame.head(8)
        if restored_bert.encode(sample)!=bert.encode(sample):raise ValueError('BERT tokenizer reload mismatch')
        # bộ tách token gốc so với bộ tách token xuất phải đồng ý sau quy tắc cắt ngắn đã cố định.
        token_stats[name]={'rows':len(frame),'truncated_reviews':sum(n>max_length for n in lengths),
                           'truncation_share':sum(n>max_length for n in lengths)/len(frame),
                           'unknown_token_share':unknown/total,'tokens_saved':total}
    guard()
    print('P4: final preservation and manifest',flush=True)
    after=input_snapshot(root,cfg)
    if after!=snapshot:raise ValueError('Previously completed input artifact changed')
    validation.update(protected41='PASS',completed_input_snapshot_files=len(snapshot),completed_inputs_preserved=True,
                      features_schema='text-only TF-IDF/BERT; label_id is separate target, rating/metadata absent',
                      preprocessing_fit='TF-IDF vocabulary/IDF and max length selected on train only',
                      pretrained_tokenizer_fit=False,feature_reload='PASS',
                      max_sequence_length=max_length,tokenization=token_stats)
    write_json(paths['report']/'validation.json',validation)
    distribution=[]
    for name,values in validation['counts'].items():
        for label,count in values['labels'].items():distribution.append({'split':name,'sentiment':label,'count':count,'share':count/values['rows']})
    pd.DataFrame(distribution).to_csv(paths['report']/'label_distribution.csv',index=False)
    preprocessing={'version':VERSION,'feature_allowlist':['text'],'audit_only_columns':[c for c in source_columns if c!='text'],
                   'raw_text_retained':True,'normalization':'P2 conservative HTML/entities/whitespace; idempotent on current input',
                   'classical':classical_info,'bert':{'repo':cfg['bert_repo'],'revision':cfg['bert_revision'],
                    'resources':resources,'declared_license':cfg['bert_declared_license'],'model_card':cfg['bert_model_card'],
                    'max_length_policy':length_policy,'length_fit_id_sha256':ordered_id_digest(frames['train'].review_id.tolist()),
                    'padding':'none in saved features; dynamic longest-in-batch at inference/training',
                    'truncation':'right, frozen from train','external_lowercase':False,
                    'pretrained_normalizer':json.loads(base.tokenizer.to_str())['normalizer'],
                    'stemming':False,'stopword_removal':False,'weights_downloaded':False,
                    'native_parallelism':False,'length_measurement':'sequential; bounded live encoding objects'}}
    write_json(paths['preprocessing']/'preprocessing.json',preprocessing)
    write_json(paths['report']/'input_preservation.json',snapshot)
    manifest={'version':cfg['version'],'source':cfg['source'],'source_sha256':cfg['source_sha256'],
              'dataset_version':'P2 Amazon 20261009_final, fixed30k','configuration':cfg,
              'configuration_sha256':sha256_file(cfg_path),'strategy':strategy,'split_sha256':split_hashes,
              'membership_sha256':sha256_file(paths['report']/'assignments.csv'),
              'excluded_rows':len(excluded),'paths':{k:p.relative_to(root).as_posix() for k,p in paths.items()},
              'implementation_sha256':{p:sha256_file(root/p) for p in ['src/data/split.py','src/preprocessing/english.py','src/preprocessing/bert.py','scripts/prepare_p4.py']},
              'train_ids_sha256':ordered_id_digest(frames['train'].review_id.tolist()),
              'output_sha256':{p.relative_to(root).as_posix():sha256_file(p) for directory in paths.values()
                               for p in sorted(directory.rglob('*')) if p.is_file()},
              'semeval':'UNTOUCHED; source/license NOT_VERIFIED owner educational exception',
              'models_trained':False,'classifier_predictions_created':False,'gold_labels_created':False,
              'runtime_seconds':time.monotonic()-started,'resources':process_memory()}
    write_json(paths['report']/'manifest.json',manifest)
    guard()
    return manifest


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,default=PROJECT_ROOT/'configs/p4.yaml')
    args=parser.parse_args()
    result=prepare(PROJECT_ROOT,args.config.resolve())
    print(json.dumps({'P4':'PASS','actual_counts':result['strategy']['actual_counts'],
                      'excluded_rows':result['excluded_rows'],'paths':result['paths']},indent=2))


if __name__=='__main__':main()
