"""Đồ đạc tổng hợp rõ ràng, không phải con người nhãn gán hoặc bằng chứng tử thi đo được."""

import json

from src.data.quality_audit import audit_review_pool, normalize_text, text_digest
from scripts.audit_annotation_inventory import product_fingerprint


def test_quality_duplicates_negation_qa_leakage_and_proxy_labels(tmp_path):
    assert normalize_text("  I do not like it &amp; won't buy again.\n") == "I do not like it & won't buy again."
    path = tmp_path/'reviews.jsonl'
    texts = ['Not good', 'Not good', 'NOT   good', 'Not good!', 'Great', 'Okay']
    rows = [{'review_id': f'r{i}', 'parent_asin': f'p{i}', 'text': text,
             'rating': [1, 5, 2, 4, 5, 3][i], 'timestamp': 0}
            for i, text in enumerate(texts)]
    path.write_text(''.join(json.dumps(r)+'\n' for r in rows),encoding='utf-8')
    result, clusters = audit_review_pool(path, qa_review_ids={'r4'}, qa_product_ids={'p5'},
        qa_text_keys={text_digest('not good')})
    assert result['rows'] == 6
    assert result['raw_exact_duplicates']['duplicate_excess_rows'] == 1
    assert result['normalized_duplicates']['duplicate_excess_rows'] == 2
    assert result['normalized_duplicates']['cross_product_groups'] == 1
    assert result['punctuation_candidates']['distinct_text_variant_groups'] == 1
    assert result['flags']['qa_id_or_text_rows'] == 4
    assert result['flags']['qa_product_rows'] == 1
    assert result['rating_proxy_class_counts'] == {'negative': 2, 'positive': 3, 'neutral': 1}
    assert result['missing_by_field']['user_id'] == 6
    assert result['timestamp_min_utc'].startswith('1970-01-01')
    assert clusters and not result['training_dataset_created']
    assert [json.loads(line)['text'] for line in path.read_text().splitlines()] == texts


def test_invalid_required_values_and_metadata_fingerprint(tmp_path):
    path = tmp_path/'bad.jsonl'
    path.write_text(json.dumps({'review_id':'r','parent_asin':'p','text':'not empty','rating':True})+'\n')
    result, _ = audit_review_pool(path, qa_review_ids=set(),qa_product_ids=set(),qa_text_keys=set())
    assert result['flags']['invalid_required_record'] == 1
    assert not result['rating_proxy_class_counts']
    a={'title':'Notebook','categories':'["Laptops"]'}
    assert product_fingerprint(a) == product_fingerprint({**a,'categories':['Laptops']})
    assert product_fingerprint(a) != product_fingerprint({**a,'title':'Notebook charger'})
