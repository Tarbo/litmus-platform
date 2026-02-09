from app.core.assignment import deterministic_bucket
from app.core.statistics import calculate_sample_size


def test_sample_size_increases_when_mde_gets_smaller():
    larger_mde = calculate_sample_size(0.1, 0.1, 0.05, 0.8)
    smaller_mde = calculate_sample_size(0.1, 0.05, 0.05, 0.8)
    assert smaller_mde > larger_mde


def test_deterministic_bucket_stable():
    one = deterministic_bucket('experiment:user-123')
    two = deterministic_bucket('experiment:user-123')
    assert one == two
    assert 0 <= one <= 1
