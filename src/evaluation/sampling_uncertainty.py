"""Khoảng dân số hữu hạn cho các mẫu xác suất QA, không phải điểm mô hình."""

import math


def _log_choose(total: int, draws: int) -> float:
    if draws < 0 or draws > total:
        return -math.inf
    draws = min(draws, total - draws)
    return math.fsum(math.log((total - i) / (draws - i)) for i in range(draws))


def hypergeom_cdf(observed: int, population: int, successes: int, sample: int) -> float:
    """P(X<=được quan sát) theo SRS mà không cần thay thế, ổn định đối với các sự kiện hiếm gặp."""
    if not 0 <= successes <= population or not 0 <= sample <= population:
        raise ValueError("Invalid hypergeometric parameters")
    low, high = max(0, sample - (population - successes)), min(sample, successes)
    if observed < low:
        return 0.0
    if observed >= high:
        return 1.0
    # PMF log-space tránh tình trạng tràn và hủy lgamma đối với quần thể lớn.
    denominator = _log_choose(population, sample)
    logs = [_log_choose(successes, x) + _log_choose(population - successes, sample - x)
            - denominator for x in range(low, observed + 1)]
    maximum = max(logs)
    return min(1.0, math.exp(maximum) * math.fsum(math.exp(x - maximum) for x in logs))


def success_total_interval(observed: int, sample: int, population: int,
                           alpha: float = 0.05) -> tuple[int, int]:
    """Đảo ngược các thử nghiệm siêu hình học có đuôi bằng nhau để đạt được thành công về tổng thể số nguyên.

    Phạm vi bảo hiểm riêng biệt >=1-alpha, có điều kiện trên cố định đúng nhãn. Bổ sung kết quả cho số lượng cao để duy trì phép tính đuôi hiếm.
    """
    if not 0 <= observed <= sample <= population or sample < 1 or not 0 < alpha < 1:
        raise ValueError("Invalid sample/coverage")
    if sample == population:
        return observed, observed
    if observed > sample // 2:
        low, high = success_total_interval(sample - observed, sample, population, alpha)
        return population - high, population - low
    tail = alpha / 2
    lower = 0
    if observed:
        left, right = observed, population - sample + observed
        while left < right:
            middle = (left + right) // 2
            if 1 - hypergeom_cdf(observed - 1, population, middle, sample) >= tail:
                right = middle
            else:
                left = middle + 1
        lower = left
    left, right = observed, population - sample + observed
    while left < right:
        middle = (left + right + 1) // 2
        if hypergeom_cdf(observed, population, middle, sample) >= tail:
            left = middle
        else:
            right = middle - 1
    return lower, left


def review_estimates(keep_n: int, keep_sample: int, keep_laptops: int,
                    reject_n: int, reject_sample: int, reject_laptops: int,
                    *, known_reject_laptops: int = 0, known_reject_non_laptops: int = 0,
                    alpha: float = 0.05) -> dict:
    """Tổng số HT và khoảng thời gian Bonferroni đồng thời từ các tầng SRS độc lập.

    Các bản ghi REJECT đã biết có trọng số 1; reject_n là khung bổ sung còn lại. Điều này hữu ích cho các cỡ mẫu phụ thuộc vào phi công mà không cần ước tính gộp đơn giản.
    """
    for n, sample, positive in [(keep_n, keep_sample, keep_laptops),
                                 (reject_n, reject_sample, reject_laptops)]:
        if not 0 <= positive <= sample <= n or sample < 1:
            raise ValueError("Invalid representative stratum")
    if min(known_reject_laptops, known_reject_non_laptops) < 0:
        raise ValueError("Invalid certainty counts")
    tp = keep_n * keep_laptops / keep_sample
    fp = keep_n - tp
    fn = known_reject_laptops + reject_n * reject_laptops / reject_sample
    tn = known_reject_non_laptops + reject_n - (fn - known_reject_laptops)
    def ratios(t: float, f: float) -> dict:
        return {"precision": t / keep_n,
                "recall": t / (t + f) if t + f else None,
                "f1": 2*t / (keep_n + t + f) if keep_n + t + f else None}
    # Hai khoảng 97.5% -> độ phủ chung >=95%, không cần độc lập.
    t_low, t_high = success_total_interval(keep_laptops, keep_sample, keep_n, alpha / 2)
    f_low, f_high = success_total_interval(reject_laptops, reject_sample, reject_n, alpha / 2)
    f_low += known_reject_laptops
    f_high += known_reject_laptops
    low, high = ratios(t_low, f_high), ratios(t_high, f_low)
    weights = [keep_n / keep_sample, reject_n / reject_sample]
    certainty_n = known_reject_laptops + known_reject_non_laptops
    weight_sum = keep_n + reject_n + certainty_n
    squares = keep_sample*weights[0]**2 + reject_sample*weights[1]**2 + certainty_n
    return {"confusion_matrix": {"TP": tp, "FP": fp, "FN": fn, "TN": tn},
            **ratios(tp, fn),
            "confidence_level": 1-alpha,
            "intervals": {k: [low[k], high[k]] for k in low},
            "success_total_bounds": {"KEEP": [t_low, t_high], "REJECT": [f_low, f_high]},
            "sampling_weights": {"KEEP": weights[0], "REJECT_remaining": weights[1], "certainty": 1},
            "kish_effective_sample_size": weight_sum**2 / squares,
            "method": "Equal-tail exact hypergeometric inversion per random stratum at alpha/2; Bonferroni joint bounds transformed monotonically to ratios. Conditional on fixed labels and valid SRS. Kish ESS is descriptive, not ratio-specific precision."}


def reject_sample_options(population: int, pilot_n: int, pilot_fn: int) -> dict:
    """Các kịch bản lập kế hoạch, ngưỡng hoặc bảo đảm không được phê duyệt."""
    if not 0 < pilot_fn < pilot_n <= population:
        raise ValueError("Nonzero pilot prevalence needed for relative precision planning")
    p = pilot_fn / pilot_n
    options = []
    for relative_halfwidth in (1.0, 0.75, 0.5, 0.25):
        n0 = 1.959963984540054**2 * (1-p) / (p*relative_halfwidth**2)
        total = math.ceil(population*n0 / (population+n0-1))
        additional = max(1, total-pilot_n)
        options.append({"relative_halfwidth_target": relative_halfwidth,
                        "planned_total": total, "additional": additional,
                        "expected_additional_FN_at_pilot_rate": additional*p,
                        "remaining_frame_relative_halfwidth_at_pilot_rate": 1.959963984540054*math.sqrt((1-p)/(p*additional)),
                        "chance_at_least_one_FN_binomial_approx": 1-(1-p)**additional,
                        "hours_at_30_seconds_per_review": additional/120})
    return {"pilot_prevalence": p, "options": options,
            "minimum_additional_for_95pct_detection_at_pilot_rate": math.ceil(math.log(.05)/math.log1p(-p)),
            "chosen_additional": options[1]["additional"],
            "selection_rationale": "Middle total-review-budget scenario: conventional pilot-rate planning targets nominal 75% relative half-width at total1018, hence 868 new after150 existing. Correct conditional complement estimator gives nominal remaining-frame half-width81.2%, not75%; this is an annotation-budget compromise, not a guaranteed precision or recall acceptance threshold. Rare-event Wald planning is approximate; pilot-dependent n requires complement-frame estimation."}
