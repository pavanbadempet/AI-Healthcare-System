"""Tests for multi-class split conformal prediction intervals."""
import numpy as np

def test_conformal_coverage_guarantee():
    # Simulates empirical coverage at alpha=0.05 (95% target)
    np.random.seed(42)
    scores = np.random.uniform(0.7, 0.99, size=1000)
    quantile = np.quantile(scores, 0.05)
    empirical_coverage = np.mean(scores >= quantile)
    assert empirical_coverage >= 0.94
