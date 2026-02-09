import math
from typing import NamedTuple


class ZTestResult(NamedTuple):
    z_score: float
    p_value: float


class Interval(NamedTuple):
    lower: float
    upper: float


def calculate_sample_size(baseline_rate: float, mde: float, alpha: float, power: float) -> int:
    # Two-proportion approximation for balanced groups.
    p1 = baseline_rate
    p2 = min(baseline_rate + mde, 0.999)
    p_bar = (p1 + p2) / 2

    z_alpha = 1.96 if alpha <= 0.05 else 1.64
    z_beta = 0.84 if power >= 0.8 else 0.52

    numerator = (z_alpha * math.sqrt(2 * p_bar * (1 - p_bar)) + z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2
    denominator = max((p2 - p1) ** 2, 1e-12)
    per_group = max(1, math.ceil(numerator / denominator))
    return per_group * 2


def _normal_cdf(value: float) -> float:
    return 0.5 * (1 + math.erf(value / math.sqrt(2)))


def two_proportion_z_test(
    control_conversions: int,
    control_exposures: int,
    treatment_conversions: int,
    treatment_exposures: int,
) -> ZTestResult:
    if control_exposures == 0 or treatment_exposures == 0:
        return ZTestResult(z_score=0.0, p_value=1.0)

    p_control = control_conversions / control_exposures
    p_treatment = treatment_conversions / treatment_exposures
    pooled = (control_conversions + treatment_conversions) / (control_exposures + treatment_exposures)
    std_error = math.sqrt(max(pooled * (1 - pooled) * ((1 / control_exposures) + (1 / treatment_exposures)), 1e-12))
    z_score = (p_treatment - p_control) / std_error
    p_value = max(0.0, min(1.0, 2 * (1 - _normal_cdf(abs(z_score)))))
    return ZTestResult(z_score=z_score, p_value=p_value)


def uplift_confidence_interval(
    control_conversions: int,
    control_exposures: int,
    treatment_conversions: int,
    treatment_exposures: int,
    confidence_level: float = 0.95,
) -> Interval:
    if control_exposures == 0 or treatment_exposures == 0:
        return Interval(lower=0.0, upper=0.0)

    p_control = control_conversions / control_exposures
    p_treatment = treatment_conversions / treatment_exposures
    uplift = p_treatment - p_control

    # Normal approximation interval for difference in proportions.
    se = math.sqrt(
        max(
            (p_control * (1 - p_control) / control_exposures)
            + (p_treatment * (1 - p_treatment) / treatment_exposures),
            1e-12,
        )
    )
    z = 1.96 if confidence_level >= 0.95 else 1.64
    margin = z * se
    return Interval(lower=uplift - margin, upper=uplift + margin)


def confidence_from_p_value(p_value: float) -> float:
    return round(max(0.0, min(0.9999, 1 - p_value)), 4)


def diff_in_diff(
    pre_control_rate: float,
    post_control_rate: float,
    pre_treatment_rate: float,
    post_treatment_rate: float,
) -> float:
    return round((post_treatment_rate - pre_treatment_rate) - (post_control_rate - pre_control_rate), 6)
