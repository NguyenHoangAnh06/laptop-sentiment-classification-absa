"""Kiểm tra mức độ bao phủ của quần thể hữu hạn chỉ sử dụng quần thể tổng hợp."""

import math
import pytest

from src.evaluation.sampling_uncertainty import (
    hypergeom_cdf, success_total_interval, review_estimates, reject_sample_options)


def test_cdf_matches_combinatorial_distribution():
    for total in range(2, 16):
        for sample in range(1, total + 1):
            for positives in range(total + 1):
                for k in (0, sample // 2, sample):
                    exact = sum(math.comb(positives, x) * math.comb(total-positives, sample-x)
                                for x in range(max(0, sample-(total-positives)), min(k, positives, sample)+1)) / math.comb(total, sample)
                    assert hypergeom_cdf(k, total, positives, sample) == pytest.approx(exact, abs=1e-12)


def test_intervals_have_at_least_nominal_coverage_small_population():
    for sample in (2, 5, 10):
        total = 12
        bounds = [success_total_interval(k, sample, total) for k in range(sample+1)]
        for positives in range(total+1):
            coverage = sum(math.comb(positives,k)*math.comb(total-positives,sample-k)/math.comb(total,sample)
                           for k in range(max(0,sample-(total-positives)),min(sample,positives)+1)
                           if bounds[k][0] <= positives <= bounds[k][1])
            assert coverage >= .95 - 1e-12
    assert success_total_interval(4, 12, 12) == (4, 4)


def test_weighted_metrics_and_rare_event_bounds():
    result = review_estimates(408480,150,150,43478204,150,1)
    assert result['recall'] == pytest.approx(.5849344217028923)
    assert result['f1'] == pytest.approx(.7381181374992468)
    assert result['success_total_bounds'] == {'KEEP':[396722,408480], 'REJECT':[3646,1816710]}
    assert result['intervals']['recall'][0] < .2
    assert result['intervals']['recall'][1] > .99
    zero = review_estimates(100,10,10,1000,10,0)
    assert zero['recall']==1 and zero['intervals']['recall'][0]<1


def test_complement_estimator_uses_pilot_as_certainty_not_naive_pool():
    result=review_estimates(100,10,10,998,2,0,known_reject_laptops=1,known_reject_non_laptops=1)
    assert result['confusion_matrix']=={'TP':100,'FP':0,'FN':1,'TN':999}
    assert result['recall']==pytest.approx(100/101)
    assert result['intervals']['recall'][1] <= 100/101


def test_planning_is_derived_and_reports_cost():
    result=reject_sample_options(43478204,150,1)
    assert result['chosen_additional']==868
    assert result['minimum_additional_for_95pct_detection_at_pilot_rate']==448
    assert result['options'][1]['planned_total']==1018
    with pytest.raises(ValueError):
        reject_sample_options(1000,150,0)
    with pytest.raises(ValueError):
        success_total_interval(2,1,100)
