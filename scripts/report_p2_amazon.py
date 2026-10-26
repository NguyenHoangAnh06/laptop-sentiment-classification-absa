"""Report/verify đã lưu kết quả đầu ra P2 mà không cần xử lý lại kho dữ liệu ứng viên."""

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

from src.config import PROJECT_ROOT
from src.data.acquisition import sha256_file
from src.data.cleaning import clean_review
from src.data.labeling import LABEL_TO_ID, rating_label
from src.data.p2_pipeline import load_qa_guards
from src.data.quality_audit import text_digest


def report_p2(run: Path, output: Path) -> dict:
    """Xác thực các bộ bảo vệ contract/leakage và xuất bảng thương hiệu before/after."""
    run, output = run.resolve(), output.resolve()
    if not output.is_relative_to((PROJECT_ROOT/'reports').resolve()):
        raise ValueError('Output must be under reports')
    if output.exists():
        raise FileExistsError('Use a new report directory')
    manifest = json.loads((run/'manifest.json').read_text(encoding='utf-8'))
    clean_path = PROJECT_ROOT/'data/processed/laptop_reviews.parquet'
    if sha256_file(clean_path) != manifest['clean_parquet_sha256']:
        raise ValueError('Processed dataset hash differs from manifest')
    rows = pq.read_table(clean_path).to_pylist()
    noise = pq.read_table(run/'label_noise_candidates.parquet').to_pylist()
    qa_ids, qa_keys = load_qa_guards([PROJECT_ROOT/p for p in manifest['qa_sources']])
    keys, ids = {r['clean_text_sha256'] for r in rows}, {r['review_id'] for r in rows}
    assert len(keys) == len(ids) == len(rows) == manifest['selection']['actual']
    assert not ids & qa_ids and not {bytes.fromhex(k) for k in keys} & qa_keys
    assert not ids & {r['review_id'] for r in noise}
    assert not keys & {r['clean_text_sha256'] for r in noise}
    assert all(r['text'] == clean_review(r['raw_text']) and r['text'].strip() for r in rows)
    assert all(r['sentiment'] == rating_label(r['rating']) and r['label_id'] == LABEL_TO_ID[r['sentiment']] for r in rows)
    assert all(text_digest(r['text'].casefold()).hex() == r['clean_text_sha256'] for r in rows)
    assert all(r['language'] == 'en' and r['language_detector_score'] >= .9 for r in rows)
    assert all(r['annotation_status'] == 'UNANNOTATED_DIAGNOSTIC_NOT_GOLD' for r in noise)
    assert Counter(r['sentiment'] for r in rows) == manifest['proxy_counts']
    assert not manifest['splits_created'] and not manifest['models_trained'] and not manifest['gold_labels_created']
    protected = json.loads((PROJECT_ROOT/'reports/tables/p1_recall_brand_preservation.json').read_text(encoding='utf-8'))['files']
    preservation = {path: sha256_file(PROJECT_ROOT/path) == digest for path,digest in protected.items()}
    assert all(preservation.values())
    for name,digest in manifest['implementation_sha256'].items():
        assert sha256_file(PROJECT_ROOT/'src/data'/name) == digest
    before = manifest['brand_before']['review_counts']
    after = manifest['brand_after']['review_counts']
    source_brands = pd.read_csv(PROJECT_ROOT/'reports/tables/p1_brand_diversity_v1/brands.csv',keep_default_na=False)
    products_before = dict(zip(source_brands['brand'], source_brands['products']))
    products_after = manifest['brand_after']['product_counts']
    brand_rows = [{'brand': brand,'before_reviews': before.get(brand,0), 'after_reviews':after.get(brand,0),
                   'before_products':products_before.get(brand,0),'after_products':products_after.get(brand,0),
                   'before_review_share':before.get(brand,0)/manifest['brand_before']['rows'],
                   'after_review_share':after.get(brand,0)/len(rows)} for brand in sorted(set(before)|set(after))]
    frame = pd.DataFrame(brand_rows)
    frame['review_share_change_pp'] = 100*(frame['after_review_share']-frame['before_review_share'])
    frame = frame.sort_values(['after_reviews','brand'],ascending=[False,True])
    assert frame['before_reviews'].sum()==408480 and frame['after_reviews'].sum()==len(rows)
    with (PROJECT_ROOT/'reports/tables/p1_brand_diversity_v1/products.csv').open(encoding='utf-8-sig',newline='') as handle:
        products = list(csv.DictReader(handle))
    metadata_flags = {'empty_title_products':sum(not r['title'].strip() for r in products),
                      'metadata_title_disagreement_products':sum(r['metadata_title_disagreement'].casefold()=='true' for r in products),
                      'limits':'Existing saved metadata flags reused; no manufacturer/source claims or invented specs.'}
    output.mkdir(parents=True)
    frame.to_csv(output/'brand_before_after.csv',index=False,encoding='utf-8')
    pd.DataFrame([{'sentiment':k,'label_id':LABEL_TO_ID[k],'reviews':manifest['proxy_counts'][k],
                   'percentage':manifest['proxy_percentages'][k]} for k in LABEL_TO_ID]).to_csv(output/'label_distribution.csv',index=False)
    missed = frame[frame.after_reviews==0]
    flags = Counter(flag for r in rows for flag in r['quality_flags'])
    result = {'validation':'PASS','protected_files':len(preservation),'preservation':preservation,
              'clean_rows':len(rows),'products':manifest['brand_after']['products'],'proxy_counts':manifest['proxy_counts'],
              'short_under_5_words_final':sum(len(r['text'].split())<5 for r in rows),
              'known_html_tag_residuals':sum(bool(re.search(r'<\s*/?\s*(?:br|p|div|span|b|strong|a)\b[^>]*>',r['text'],re.I)) for r in rows),
              'retained_quality_flags':dict(flags),'noise_candidates':len(noise),
              'absent_brand_categories':len(missed),'candidate_reviews_in_absent_brand_categories':int(missed.before_reviews.sum()),
              'candidate_review_share_in_absent_categories':float(missed.before_reviews.sum()/408480),
              'product_metadata_flags':metadata_flags,'source_manifest_sha256':sha256_file(run/'manifest.json'),
              'dataset_sha256':manifest['clean_parquet_sha256'],'qa_id_text_overlap':0,'noise_id_text_overlap':0,
              'true_language_error_rate':'NOT_MEASURED; offline detector selected English, not human verification',
              'true_rating_text_disagreement_rate':'NOT_MEASURED; diagnostic cues only, no human sentiment labels',
              'splits_created':False,'models_trained':False,
              'artifact_sha256':{p.relative_to(PROJECT_ROOT).as_posix():sha256_file(p)
                                 for p in [run/'label_noise_candidates.csv',run/'label_noise_candidates.parquet',
                                           run/'near_duplicate_pairs.json',output/'brand_before_after.csv',output/'label_distribution.csv']}}
    (output/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return result


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir',type=Path,default=Path('data/interim/p2/20261009_final'))
    parser.add_argument('--output-dir',type=Path,required=True)
    args=parser.parse_args()
    result=report_p2(args.run_dir,args.output_dir)
    print(json.dumps({k:result[k] for k in ('validation','protected_files','clean_rows','products','noise_candidates','known_html_tag_residuals','absent_brand_categories')},indent=2))


if __name__=='__main__':
    main()
