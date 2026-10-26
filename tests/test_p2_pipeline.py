"""Chỉ các thiết bị cố định P2 tổng hợp; không bao giờ đo con người QA/gold hoặc đo khối lượng."""

import json
import sqlite3

import pytest

from src.data.cleaning import clean_review, quality_flags
from src.data.labeling import LABEL_TO_ID, noise_reasons, rating_label
from src.data.near_duplicates import audit_near_duplicates
from src.data.p2_pipeline import reserve_noise, selection_key, stage_candidates, write_parquet
from src.data.quality_audit import text_digest


def test_cleaning_keeps_negation_boundaries_urls_unknown_tags_and_raw_input():
    raw = "<p>I do <b>not</b> like it.<br>It won't work &amp; never starts.</p> https://example.org <3"
    result = clean_review(raw)
    assert result == "I do not like it. It won't work & never starts. https://example.org <3"
    assert '<b>not</b>' in raw
    assert clean_review('good<div>not bad</div>') == 'good not bad'
    assert clean_review('   \t\n ') == ''
    assert clean_review('battery <custom>very poor</custom>') == 'battery <custom>very poor</custom>'
    assert clean_review('not&lt;br /&gt;good &amp;amp; never works') == 'not good & never works'
    assert clean_review('&lt;custom/&gt;') == '<custom/>'
    assert 'url_present_retained' in quality_flags(result)


@pytest.mark.parametrize('rating,label', [(1,'negative'),(2,'negative'),(3,'neutral'),(4,'positive'),(5,'positive')])
def test_proxy_boundaries(rating, label):
    assert rating_label(rating) == label
    assert LABEL_TO_ID == {'negative':0,'neutral':1,'positive':2}


@pytest.mark.parametrize('rating', [True,False,0,6,3.0,None,'5'])
def test_proxy_invalid(rating):
    with pytest.raises(ValueError):
        rating_label(rating)


def test_stage_dedup_mixed_labels_qa_and_source_integrity(tmp_path):
    metadata = {p:{'brand_normalized':'HP','brand_raw':'HP'} for p in ('p1','p2')}
    rows = [{'review_id':f'r{i}','parent_asin':'p1' if i<2 else 'p2','text':text,'rating':rating,'user_id':f'u{i}'}
            for i,(text,rating) in enumerate([('<b>Not good</b>',1),('not good',2),('Amazing laptop',1),
                                            ('Amazing laptop',5),('QA text',5),('',3),('Okay enough',True),
                                            ('Perfect laptop for work',4)])]
    source=tmp_path/'source.jsonl'
    source.write_text(''.join(json.dumps(r)+'\n' for r in rows),encoding='utf-8')
    original=source.read_bytes()
    database=tmp_path/'ledger.sqlite'
    result=stage_candidates(source,database,metadata,seed=42,qa_ids=set(),qa_keys={text_digest('qa text')},
                            max_memory=512000000,max_seconds=60,max_output_bytes=2000000)
    c=result['counts']
    assert c['input_rows']==8 and c['mixed_proxy_label_group_rows_quarantined']==2
    assert c['same_label_duplicate_excess_removed']==1 and c['qa_id_or_text_reserved']==1
    assert c['empty_after_cleaning']==1 and c['invalid_required_record']==1 and c['eligible_unique_groups']==2
    assert result['cross_user_same_label_groups']==1
    assert source.read_bytes()==original
    with sqlite3.connect(database) as db:
        record=json.loads(db.execute('SELECT payload FROM groups WHERE product="p1"').fetchone()[0])
    assert record['raw_text']=='<b>Not good</b>' and record['text']=='Not good'
    with pytest.raises(FileExistsError):
        stage_candidates(source,database,metadata,seed=42,qa_ids=set(),qa_keys=set(),
                         max_memory=512000000,max_seconds=60,max_output_bytes=2000000)


def test_noise_worklist_reservations_are_not_human_labels():
    rows=[{'review_id':'r1','text':'Excellent laptop, but it is defective and unusable.','rating':5},
          {'review_id':'r2','text':'The laptop works perfectly, I returned it anyway.','rating':1},
          {'review_id':'r3','text':'This is average, neither good nor bad.','rating':2},
          {'review_id':'r4','text':'Very useful laptop for ordinary office work.','rating':4}]
    kept,candidates=reserve_noise(rows,count=3,seed=42)
    assert [r['review_id'] for r in kept]==['r4']
    assert len(candidates)==3 and all(r['annotation_status']=='UNANNOTATED_DIAGNOSTIC_NOT_GOLD' for r in candidates)
    assert not noise_reasons('I do not highly recommend this laptop.',1)
    assert selection_key('r1',42)==selection_key('r1',42)!=selection_key('r1',43)


def test_near_duplicates_preserve_opposite_sentiment_and_assign_group():
    text='This laptop has a very good keyboard and screen and works well for daily office tasks every day'
    rows=[{'review_id':'a','text':text,'sentiment':'positive'},
          {'review_id':'b','text':text+' indeed','sentiment':'negative'},
          {'review_id':'c','text':'Not good','sentiment':'negative'}]
    pairs,report=audit_near_duplicates(rows,seed=42,threshold=.8)
    assert pairs and pairs[0]['same_proxy_label'] is False
    assert rows[0]['near_duplicate_group_id']==rows[1]['near_duplicate_group_id']=='a'
    assert rows[2]['near_duplicate_group_id'] is None
    assert len(rows)==3 and not report['comparison_cap_reached']


def test_parquet_roundtrip_and_no_overwrite(tmp_path):
    import pyarrow.parquet as pq
    rows=[{'review_id':'r','text':"I won't buy this again.",'sentiment':'negative','label_id':0,
           'near_duplicate_group_id':None,'quality_flags':[]}]
    path=tmp_path/'reviews.parquet'
    write_parquet(path,rows)
    assert pq.read_table(path).to_pylist()==rows
    with pytest.raises(FileExistsError):
        write_parquet(path,rows)


def test_language_and_complete_pipeline_on_synthetic_fixture(tmp_path):
    """Chạy trình phát hiện ngoại tuyến thực, sổ cái, dự trữ, lựa chọn và tải lại; không có huấn luyện."""
    import csv
    from src.data.acquisition import sha256_file
    from src.data.p2_pipeline import run_p2
    approval=tmp_path/'reports/tables/p1_owner_approval_20261009.json'
    approval.parent.mkdir(parents=True)
    approval.write_text(json.dumps({'p2_amazon_only_authorized':True,'semeval_authorized':False}))
    source=tmp_path/'fixture.jsonl'
    texts=['The screen is excellent and this laptop works very well for my daily office tasks.',
           'This computer has poor battery life and never starts correctly when I need it.',
           'The computer is average and ordinary and neither good nor bad for the price.',
           'Excelente computadora, la batería dura mucho tiempo y el teclado es muy cómodo.']
    rows=[{'review_id':f'r{i}','parent_asin':f'p{i}','text':t,'rating':[5,1,3,4][i]} for i,t in enumerate(texts)]
    source.write_text(''.join(json.dumps(r)+'\n' for r in rows),encoding='utf-8')
    metadata=tmp_path/'products.csv'
    with metadata.open('w',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=['product_id','brand_normalized','brand_raw'])
        writer.writeheader()
        writer.writerows({'product_id':f'p{i}','brand_normalized':'HP','brand_raw':'HP'} for i in range(4))
    quality=tmp_path/'quality.json'
    quality.write_text(json.dumps({'source':'fixture.jsonl','source_sha256':sha256_file(source),'qa_sources':{},'rows':4}))
    config={'output_dir':'interim','quality_audit':'quality.json','brand_products':'products.csv',
            'max_memory_bytes':512000000,'max_seconds':60,'max_output_bytes':2000000,'noise_reserve':0,
            'selection_buffer':10,'max_language_candidates':10,'language_batch_size':4,'english_min_score':.9,
            'language_min_margin':.2,'ascii_letter_min_share':.98,'max_reviews_per_product':100,
            'near_jaccard':.9,'max_near_comparisons':1000}
    data={'seed':42,'target_clean_reviews':3,'paths':{'clean_reviews':'processed/reviews.parquet'},
          'rating_to_label':{1:'negative',2:'negative',3:'neutral',4:'positive',5:'positive'}}
    first=run_p2(config,data,root=tmp_path)
    assert first['selection']['actual']==3
    assert first['language']['outcomes']['language_uncertain_or_non_english']==1
    assert first['proxy_counts']=={'negative':1,'positive':1,'neutral':1}
    assert not first['splits_created'] and not first['gold_labels_created'] and not first['models_trained']
    second=run_p2({**config,'output_dir':'interim_again'},
                  {**data,'paths':{'clean_reviews':'processed/reviews_again.parquet'}},root=tmp_path)
    assert first['clean_parquet_sha256']==second['clean_parquet_sha256']
    with pytest.raises(FileExistsError):
        run_p2(config,data,root=tmp_path)
