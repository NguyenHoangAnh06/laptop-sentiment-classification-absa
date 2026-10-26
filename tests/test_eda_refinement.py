"""Fixture số đếm tổng hợp kiểm mẫu số/support; không là bằng chứng review thật."""

from pathlib import Path

import pandas as pd
import pytest

from src.data.eda_refinement import phrase_rates, select_phrases


def counts() -> pd.DataFrame:
    rows = []
    for term, values in [('stopped working', (20, 5, 5)), ('not working', (20, 5, 5)),
                         ('dead battery', (1, 0, 0))]:
        for label, value in zip(('negative', 'neutral', 'positive'), values):
            rows.append(dict(n=2, term=term, sentiment=label, documents=value,
                             class_documents=100, total_documents=sum(values)))
    return pd.DataFrame(rows)


def test_rates_use_outside_class_denominator_and_preserve_input():
    source = counts()
    before = source.copy(deep=True)
    result = phrase_rates(source)
    row = result.query("sentiment == 'negative' and term == 'not working'").iloc[0]
    assert row.prevalence == .2
    assert row.rest_prevalence == .05  # 10/200, không 10/300 hoặc 30/300.
    assert row.outside_documents == 10 and row.outside_class_documents == 200
    assert row.prevalence_difference == pytest.approx(.15)
    pd.testing.assert_frame_equal(source, before)


def test_rare_high_lift_does_not_bypass_support_and_ties_are_stable():
    source = counts()
    a = select_phrases(source, minimum=10, top=2, pattern='working', labels=('negative',))
    b = select_phrases(source.sample(frac=1, random_state=7), minimum=10, top=2,
                       pattern='working', labels=('negative',))
    assert list(a.term) == ['not working', 'stopped working']
    pd.testing.assert_frame_equal(a, b)
    assert 'dead battery' not in select_phrases(source, minimum=10).term.tolist()


@pytest.mark.parametrize('fault', ['missing_class', 'invalid_count', 'duplicate'])
def test_inconsistent_lexical_evidence_fails_closed(fault):
    source = counts()
    if fault == 'missing_class':
        source = source.iloc[1:]
    elif fault == 'invalid_count':
        source.loc[0, 'documents'] = 101
    else:
        source = pd.concat([source, source.iloc[:1]], ignore_index=True)
    with pytest.raises(ValueError):
        phrase_rates(source)


def test_report_never_overwrites_or_writes_outside_reports(tmp_path: Path):
    from scripts.refine_p3 import build
    existing = tmp_path / 'reports/frozen'
    existing.mkdir(parents=True)
    sentinel = existing / 'sentinel.txt'
    sentinel.write_text('frozen', encoding='utf-8')
    with pytest.raises(FileExistsError):
        build(existing, root=tmp_path)
    with pytest.raises(ValueError):
        build(tmp_path / 'outside', root=tmp_path)
    assert sentinel.read_text(encoding='utf-8') == 'frozen'
    assert not (tmp_path / 'outside').exists()
