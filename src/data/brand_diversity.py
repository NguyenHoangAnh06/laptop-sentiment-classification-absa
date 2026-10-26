"""Mô tả thương hiệu của nhóm ứng viên; không bao giờ suy ra tính đại diện của thị trường."""

import json
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path
from src.data.acquisition import sha256_file
from src.data.independent_qa import write_csv
from src.data.loader import iter_jsonl

ALIASES={
    'hp':'HP','hewlett-packard':'HP','hewlett packard':'HP','hewlett packard company':'HP',
    'asus':'ASUS','asustek':'ASUS','asustek computer inc.':'ASUS',
    'lenovo':'Lenovo','dell':'Dell','acer':'Acer','apple':'Apple','msi':'MSI',
    'micro-star international':'MSI','samsung':'Samsung','lg':'LG','lg electronics':'LG',
    'microsoft':'Microsoft','toshiba':'Toshiba','gateway':'Gateway','razer':'Razer',
    'fujitsu':'Fujitsu','panasonic':'Panasonic','sony':'Sony','huawei':'Huawei',
    'chuwi':'CHUWI','jumper':'Jumper','dynabook':'Dynabook','alienware':'Alienware'}
MISSING={'','unknown','n/a','na','none','null','generic','unbranded'}


def normalize_brand(raw: object, title: str = '') -> dict:
    """Sử dụng bí danh siêu dữ liệu chính xác; gợi ý tiêu đề được giữ riêng biệt, không bao giờ ghi đè lên sự thật."""
    cleaned=' '.join(unicodedata.normalize('NFKC',raw).strip().split()) if isinstance(raw,str) else ''
    key=cleaned.casefold()
    hints=sorted({v for k,v in ALIASES.items() if re.search(r'(?<!\w)'+re.escape(k)+r'(?!\w)',title,re.I)})
    missing=key in MISSING
    ambiguous=not missing and bool(re.search(r'[/|;,]',cleaned))
    canonical='UNKNOWN' if missing else 'AMBIGUOUS' if ambiguous else ALIASES.get(key,key)
    return {'brand_raw':raw,'brand_normalized':canonical,
            'brand_status':'missing_or_generic' if missing else 'ambiguous' if ambiguous else 'metadata_alias' if key in ALIASES else 'metadata_other',
            'title_brand_hint':hints[0] if len(hints)==1 else None,
            'title_hint_ambiguous':len(hints)>1,
            'metadata_title_disagreement':bool(not missing and not ambiguous and hints and canonical not in hints)}


def _concentration(counts: Counter) -> dict:
    total=sum(counts.values()); values=sorted(counts.values(),reverse=True)
    shares=[v/total for v in values if v]
    return {'top3_share':sum(shares[:3]),'top5_share':sum(shares[:5]),
            'hhi':sum(x*x for x in shares),'shannon_entropy_nats':-sum(x*math.log(x) for x in shares),
            'effective_number_of_brands':math.exp(-sum(x*math.log(x) for x in shares))}


def analyze_brands(run: Path, output: Path) -> dict:
    """Đã lưu luồng products/valid review; báo cáo tất cả các nhãn hiệu và xuất xứ."""
    if output.exists():
        raise FileExistsError('Use a new brand-analysis directory')
    if run.resolve()==output.resolve() or run.resolve() in output.resolve().parents:
        raise ValueError('Output must be outside saved pool')
    report=json.loads((run/'report.json').read_text(encoding='utf-8'))
    for name in ('products.jsonl','laptop_valid.jsonl'):
        if sha256_file(run/name)!=report['output_sha256'][name]:
            raise ValueError('Candidate pool hash mismatch')
    products={}; raw_counts=Counter(); brand_products=Counter(); statuses=Counter()
    for _,row in iter_jsonl(run/'products.jsonl'):
        parent=row['parent_asin']
        if parent in products:
            raise ValueError('Duplicate product identifier')
        record={'product_id':parent,'title':row['title'],**normalize_brand(row.get('brand'),row['title'])}
        products[parent]=record; raw_counts[row.get('brand') or '']=raw_counts.get(row.get('brand') or '',0)+1
        brand_products[record['brand_normalized']]+=1; statuses[record['brand_status']]+=1
    brand_reviews=Counter(); per_product=Counter(); reviews=0
    for _,row in iter_jsonl(run/'laptop_valid.jsonl'):
        parent=row['parent_asin']
        if parent not in products or row.get('brand')!=products[parent]['brand_raw']:
            raise ValueError('Review metadata linkage mismatch')
        brand_reviews[products[parent]['brand_normalized']]+=1; per_product[parent]+=1; reviews+=1
    expected=report['groups']['laptop']
    if len(products)!=expected['candidate_products'] or reviews!=expected['valid_reviews']:
        raise ValueError('Pool row counts mismatch')
    for parent,record in products.items():
        record['review_count']=per_product[parent]
    brands=sorted(brand_products,key=lambda b:(-brand_reviews[b],-brand_products[b],b))
    table=[{'brand':b,'products':brand_products[b],'reviews':brand_reviews[b],
            'product_share':brand_products[b]/len(products),'review_share':brand_reviews[b]/reviews,
            'review_minus_product_share':brand_reviews[b]/reviews-brand_products[b]/len(products)} for b in brands]
    unknown_products=sum(brand_products[b] for b in ('UNKNOWN','AMBIGUOUS'))
    unknown_reviews=sum(brand_reviews[b] for b in ('UNKNOWN','AMBIGUOUS'))
    top=per_product.most_common(20)
    result={'status':'ANALYSIS_COMPLETE_ACCEPTANCE_NEEDS_REVIEW','products':len(products),'valid_reviews':reviews,
            'raw_brand_strings_nonmissing':sum(bool(k) for k in raw_counts),
            'normalized_metadata_brand_categories':len(brands),
            'known_metadata_brand_categories':sum(b not in ('UNKNOWN','AMBIGUOUS') for b in brands),
            'status_product_counts':dict(statuses),
            'unknown_or_ambiguous_product_share':unknown_products/len(products),
            'unknown_or_ambiguous_review_share':unknown_reviews/reviews,
            'metadata_title_disagreement_products':sum(r['metadata_title_disagreement'] for r in products.values()),
            'missing_with_single_title_hint':sum(r['brand_normalized']=='UNKNOWN' and r['title_brand_hint'] is not None for r in products.values()),
            'product_concentration':_concentration(brand_products),'review_concentration':_concentration(brand_reviews),
            'product_review_total_variation':.5*sum(abs(r['review_minus_product_share']) for r in table),
            'products_without_valid_reviews':sum(not per_product[p] for p in products),
            'largest_product':{'product_id':top[0][0],'reviews':top[0][1],'review_share':top[0][1]/reviews},
            'top10_product_review_share':sum(n for _,n in per_product.most_common(10))/reviews,
            'top100_product_review_share':sum(n for _,n in per_product.most_common(100))/reviews,
            'source_hashes':{name:sha256_file(run/name) for name in ('products.jsonl','laptop_valid.jsonl','report.json')},
            'normalization':'NFKC/whitespace/casefold, exact alias map; other metadata brands retained, multi-brand delimiter strings ambiguous. Metadata is details.Brand from saved index, never store. Title hints do not replace metadata; reseller/manufacturer differences possible.',
            'alias_map':ALIASES,'acceptance':'No approved brand thresholds found; analysis complete, preservation of final clean-data brand diversity remains pending P2. Candidate brand labels are not independently validated manufacturer identities.'}
    output.mkdir(parents=True)
    write_csv(output/'brands.csv',list(table[0]),table)
    write_csv(output/'products.csv',list(next(iter(products.values()))),list(products.values()))
    write_csv(output/'raw_brands.csv',['brand_raw','products'],[{'brand_raw':k,'products':v} for k,v in raw_counts.most_common()])
    write_csv(output/'top_products.csv',['product_id','reviews','review_share'],[{'product_id':p,'reviews':n,'review_share':n/reviews} for p,n in top])
    (output/'summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    _charts(table,products,output)
    return result


def _charts(table: list[dict], products: dict, output: Path) -> None:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size':10,'svg.hashsalt':'p1-brand-diversity'})
    def save(fig,name):
        fig.tight_layout(); fig.savefig(output/f'{name}.png',dpi=150)
        fig.savefig(output/f'{name}.svg',metadata={'Date':None}); plt.close(fig)
    for column in ('products','reviews'):
        rows=sorted(table,key=lambda r:r[column],reverse=True)[:12][::-1]
        fig,ax=plt.subplots(figsize=(9,5)); ax.barh([r['brand'] for r in rows],[r[column] for r in rows],color='#246b9b')
        display_column = {'products': 'sản phẩm', 'reviews': 'review'}.get(column, column)
        ax.set_title(f'Thương hiệu siêu dữ liệu dẫn đầu theo {display_column} — tập ứng viên'); ax.set_xlabel(display_column)
        save(fig,f'top_brands_{column}')
    rows=table[:10]; positions=list(range(len(rows)))
    fig,ax=plt.subplots(figsize=(10,5))
    ax.bar([i-.2 for i in positions],[100*r['product_share'] for r in rows],.4,label='Sản phẩm')
    ax.bar([i+.2 for i in positions],[100*r['review_share'] for r in rows],.4,label='Review hợp lệ')
    ax.set_xticks(positions,[r['brand'] for r in rows],rotation=30,ha='right'); ax.set_ylabel('Tỷ lệ (%)'); ax.legend()
    ax.set_title('Tỷ lệ sản phẩm và review theo thương hiệu siêu dữ liệu'); save(fig,'product_vs_review_share')
    fig,ax=plt.subplots(figsize=(9,4))
    for column,label in [('product_share','Sản phẩm'),('review_share','Review')]:
        shares=sorted([r[column] for r in table],reverse=True); cumulative=[]; total=0
        for x in shares: total+=x; cumulative.append(total*100)
        ax.plot(range(1,len(shares)+1),cumulative,label=label)
    ax.set_xlabel('Xếp hạng thương hiệu (được sắp xếp riêng)'); ax.set_ylabel('Tỷ lệ tích lũy (%)'); ax.set_title('Mức tập trung thương hiệu siêu dữ liệu'); ax.legend()
    save(fig,'brand_concentration')
    labels=['Đã xác định từ siêu dữ liệu','Chưa xác định','Mơ hồ']; groups=['known','UNKNOWN','AMBIGUOUS']
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    for ax,column in zip(axes,['products','reviews']):
        totals=[sum(r[column] for r in table if (r['brand'] not in ('UNKNOWN','AMBIGUOUS') if g=='known' else r['brand']==g)) for g in groups]
        ax.bar(labels,[100*n/sum(totals) for n in totals],color=['#246b9b','#b76a20','#a43743']); ax.set_ylabel('Tỷ lệ (%)'); ax.set_title({'products': 'Sản phẩm', 'reviews': 'Review'}.get(column, column))
    save(fig,'unknown_brand_distribution')
