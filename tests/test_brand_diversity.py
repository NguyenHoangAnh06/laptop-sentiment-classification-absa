"""Các quy tắc và số lượng thương hiệu đã được kiểm tra trên siêu dữ liệu tổng hợp, không phải gold nhãn thực."""
import json
import pytest
from src.data.acquisition import sha256_file
from src.data.brand_diversity import normalize_brand,analyze_brands


@pytest.mark.parametrize('raw,expected',[(' HP ','HP'),('Hewlett-Packard','HP'),('Asus','ASUS'),('ＡＳＵＳ','ASUS'),('Dell','Dell'),('Obscure Brand','obscure brand'),(None,'UNKNOWN'),('Generic','UNKNOWN'),('HP/Dell','AMBIGUOUS')])
def test_brand_normalization(raw,expected):
    assert normalize_brand(raw)['brand_normalized']==expected


def test_title_never_overwrites_metadata_or_invents_certainty():
    assert normalize_brand(None,'HP laptop')['brand_normalized']=='UNKNOWN'
    assert normalize_brand(None,'HP laptop')['title_brand_hint']=='HP'
    assert normalize_brand(None,'Dell or HP laptop')['title_hint_ambiguous']
    result=normalize_brand('HIDevolution','ASUS laptop')
    assert result['brand_normalized']=='hidevolution' and result['metadata_title_disagreement']


def test_full_brand_counts_and_artifacts(tmp_path):
    run=tmp_path/'run';run.mkdir()
    products=[{'parent_asin':'A','title':'HP laptop','brand':'Hewlett-Packard'},
              {'parent_asin':'B','title':'ASUS laptop','brand':'Asus'},
              {'parent_asin':'C','title':'HP laptop','brand':None}]
    reviews=[{'parent_asin':'A','brand':'Hewlett-Packard'}]*3+[{'parent_asin':'B','brand':'Asus'}]
    for name,rows in [('products.jsonl',products),('laptop_valid.jsonl',reviews)]:
        (run/name).write_text(''.join(json.dumps(r)+'\n' for r in rows))
    (run/'report.json').write_text(json.dumps({'output_sha256':{p.name:sha256_file(p) for p in run.iterdir()},'groups':{'laptop':{'candidate_products':3,'valid_reviews':4}}}))
    out=tmp_path/'brands';r=analyze_brands(run,out)
    assert r['unknown_or_ambiguous_product_share']==pytest.approx(1/3)
    assert r['unknown_or_ambiguous_review_share']==0
    assert r['products_without_valid_reviews']==1
    assert r['largest_product']['review_share']==.75
    assert len(list(out.glob('*.png')))==5 and len(list(out.glob('*.svg')))==5
    assert (out/'brands.csv').exists() and (out/'products.csv').exists()
    with pytest.raises(FileExistsError):analyze_brands(run,out)
