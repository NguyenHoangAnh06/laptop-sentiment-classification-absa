"""đồ đạc EDA tổng hợp; không có mẫu con người nhãn hoặc review thực."""

import pandas as pd
import pytest

from src.data.eda import build_tables, lexical_tables, wilson_interval


@pytest.fixture
def reviews():
    return pd.DataFrame([
        dict(review_id='a',text='not good battery battery',rating=1,sentiment='negative',
             parent_asin='p1',brand_normalized='Brand A',timestamp=1577836800000,
             helpful_vote=2,verified_purchase=True,clean_text_sha256='ha'),
        dict(review_id='b',text='good screen',rating=5,sentiment='positive',
             parent_asin='p1',brand_normalized='Brand A',timestamp=1609459200000,
             helpful_vote=0,verified_purchase=False,clean_text_sha256='hb'),
        dict(review_id='c',text='battery is not good',rating=3,sentiment='neutral',
             parent_asin='p2',brand_normalized='Unknown',timestamp=1609459200000,
             helpful_vote=0,verified_purchase=True,clean_text_sha256='hc'),
    ])


def test_eda_denominators_and_preserves_inputs(reviews):
    original=reviews.copy(deep=True)
    summary,t=build_tables(reviews,min_documents=1)
    pd.testing.assert_frame_equal(reviews,original)
    assert summary['rows']==3 and summary['products']==2
    assert summary['short_under_5_words']==3
    assert t['sentiment']['review_share'].sum()==pytest.approx(1)
    battery=t['themes'].query("theme=='battery' and sentiment=='negative'").iloc[0]
    assert battery.mention_reviews==1 and battery.within_class_share==1
    assert battery.overall_share==pytest.approx(2/3)
    assert t['products'].set_index('parent_asin').loc['p1','negative_share']==.5
    assert not t['products'].sufficient_support.any()
    assert t['length_histogram'].reviews.sum()==3


def test_lexical_document_frequency_negation_and_contiguous_ngrams(reviews):
    t=lexical_tables(reviews,1)['frequent_terms'].set_index(['n','term'])
    assert t.loc[(1,'battery'),'documents']==2  # số lần lặp lại token once/review
    assert t.loc[(1,'not'),'documents']==2
    assert t.loc[(2,'not good'),'documents']==2
    assert (2,'battery not') not in t.index  # không loại bỏ mật khẩu cầu nối
    assert lexical_tables(reviews,4)['lexical_by_class'].empty


def test_repeatable_tables_and_group_support(reviews):
    a,ta=build_tables(reviews,1);b,tb=build_tables(reviews,1)
    assert a==b
    for key in ta:pd.testing.assert_frame_equal(ta[key],tb[key])
    assert ta['months'].reviews.sum()==3
    assert ta['verified'].reviews.sum()==3


@pytest.mark.parametrize('success,total',[(0,100),(100,100),(50,100)])
def test_wilson_boundaries(success,total):
    low,high=wilson_interval(success,total)
    assert -1e-14<=low<=success/total<=high<=1+1e-14
    if success==50:assert low==pytest.approx(1-high)


def test_invalid_inputs_fail(reviews):
    with pytest.raises(ValueError):wilson_interval(2,1)
    with pytest.raises(ValueError):build_tables(reviews.drop(columns='text'))
    with pytest.raises(ValueError):build_tables(reviews.iloc[:0])
    reviews.loc[0,'sentiment']='invented'
    with pytest.raises(ValueError):build_tables(reviews)


def test_charts_handle_sparse_time_groups(reviews,tmp_path):
    from scripts.analyze_p3 import plot_tables
    _,tables=build_tables(reviews,1)
    paths=plot_tables(tables,tmp_path)
    assert len(paths)==14
    assert all((tmp_path/p).stat().st_size>500 for p in paths)
