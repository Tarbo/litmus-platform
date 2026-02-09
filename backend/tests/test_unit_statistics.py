from app.core.assignment import deterministic_bucket
from app.core.statistics import (
    calculate_sample_size,
    confidence_from_p_value,
    diff_in_diff,
    two_proportion_z_test,
    uplift_confidence_interval,
)


def test_sample_size_increases_when_mde_gets_smaller():
    larger_mde = calculate_sample_size(0.1, 0.1, 0.05, 0.8)
    smaller_mde = calculate_sample_size(0.1, 0.05, 0.05, 0.8)
    assert smaller_mde > larger_mde


def test_deterministic_bucket_stable():
    one = deterministic_bucket('experiment:user-123')
    two = deterministic_bucket('experiment:user-123')
    assert one == two
    assert 0 <= one <= 1


def test_z_test_detects_positive_uplift_signal():
    result = two_proportion_z_test(
        control_conversions=100,
        control_exposures=1000,
        treatment_conversions=150,
        treatment_exposures=1000,
    )
    assert result.z_score > 0
    assert result.p_value < 0.01


def test_uplift_interval_contains_observed_uplift():
    interval = uplift_confidence_interval(
        control_conversions=200,
        control_exposures=1000,
        treatment_conversions=240,
        treatment_exposures=1000,
    )
    observed_uplift = 0.24 - 0.20
    assert interval.lower <= observed_uplift <= interval.upper


def test_diff_in_diff_works_for_pre_post_rates():
    did = diff_in_diff(0.10, 0.11, 0.10, 0.14)
    assert did == 0.03


def test_confidence_from_p_value():
    assert confidence_from_p_value(0.2) == 0.8
