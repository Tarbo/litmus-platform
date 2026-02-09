import math


def calculate_sample_size(baseline_rate: float, mde: float, alpha: float, power: float) -> int:
    # Simple two-proportion approximation to keep sizing transparent.
    p1 = baseline_rate
    p2 = min(baseline_rate + mde, 0.999)
    p_bar = (p1 + p2) / 2

    z_alpha = 1.96 if alpha <= 0.05 else 1.64
    z_beta = 0.84 if power >= 0.8 else 0.52

    numerator = (z_alpha * math.sqrt(2 * p_bar * (1 - p_bar)) + z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2
    denominator = (p2 - p1) ** 2
    per_group = max(1, math.ceil(numerator / denominator))
    return per_group * 2


def approximate_confidence(exposures: int, conversions: int, mde: float) -> float:
    if exposures == 0:
        return 0.0
    observed_rate = conversions / exposures
    signal = abs(observed_rate - mde)
    confidence = min(0.99, 0.5 + signal)
    return round(confidence, 4)
