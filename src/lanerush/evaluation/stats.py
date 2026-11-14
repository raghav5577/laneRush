"""Statistical tests for KPI comparison."""

from __future__ import annotations

import math


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def std(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    m = mean(values)
    return math.sqrt(sum((v - m) ** 2 for v in values) / (len(values) - 1))


def confidence_interval_t(values: list[float], confidence: float = 0.95) -> tuple[float, float]:
    """95% CI using t-distribution (two-tailed)."""
    import math

    n = len(values)
    if n < 2:
        m = mean(values)
        return m, m
    m = mean(values)
    s = std(values)
    # t critical value approximation for common n
    # For n >= 30 use z=1.96; otherwise use a simple lookup
    t_crit = _t_critical(n - 1, confidence)
    margin = t_crit * s / math.sqrt(n)
    return m - margin, m + margin


def _t_critical(df: int, confidence: float = 0.95) -> float:
    """Rough t-critical value. Use scipy if available, otherwise fallback."""
    try:
        from scipy.stats import t  # noqa: PLC0415

        alpha = 1 - confidence
        return float(t.ppf(1 - alpha / 2, df))
    except ImportError:
        # Fallback for common cases
        if df >= 120:
            return 1.960
        if df >= 60:
            return 2.000
        if df >= 30:
            return 2.042
        if df >= 20:
            return 2.086
        if df >= 10:
            return 2.228
        if df >= 5:
            return 2.571
        return 2.776


def wilcoxon_signed_rank_p(a: list[float], b: list[float]) -> float:
    """Paired Wilcoxon signed-rank test p-value (two-sided)."""
    try:
        from scipy.stats import wilcoxon  # noqa: PLC0415

        diffs = [ai - bi for ai, bi in zip(a, b)]
        if all(d == 0 for d in diffs):
            return 1.0
        stat, p = wilcoxon(diffs)
        return float(p)
    except ImportError:
        return float("nan")


def paired_t_p(a: list[float], b: list[float]) -> float:
    """Paired t-test p-value (two-sided)."""
    try:
        from scipy.stats import ttest_rel  # noqa: PLC0415

        stat, p = ttest_rel(a, b)
        return float(p)
    except ImportError:
        return float("nan")


def percent_change(baseline: float, treatment: float) -> float:
    """% change from baseline to treatment."""
    if baseline == 0:
        return float("nan")
    return 100.0 * (treatment - baseline) / baseline
