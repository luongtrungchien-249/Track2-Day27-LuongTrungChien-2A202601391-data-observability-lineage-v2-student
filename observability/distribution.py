"""Distribution drift detection using KS-test, PSI, and robust statistical ratios."""
from __future__ import annotations

from typing import Any, Iterable

import numpy as np


def _calculate_psi(current: np.ndarray, baseline: np.ndarray, num_buckets: int = 5) -> float:
    """Calculate Population Stability Index (PSI)."""
    if current.size < 5 or baseline.size < 5:
        return 0.0
    try:
        percentiles = np.linspace(0, 100, num_buckets + 1)
        bucket_bounds = np.percentile(baseline, percentiles)
        bucket_bounds[0] = -np.inf
        bucket_bounds[-1] = np.inf

        base_counts, _ = np.histogram(baseline, bins=bucket_bounds)
        cur_counts, _ = np.histogram(current, bins=bucket_bounds)

        # Smooth zero counts with epsilon
        base_pct = np.maximum(base_counts / baseline.size, 1e-4)
        cur_pct = np.maximum(cur_counts / current.size, 1e-4)

        base_pct /= base_pct.sum()
        cur_pct /= cur_pct.sum()

        psi_val = np.sum((cur_pct - base_pct) * np.log(cur_pct / base_pct))
        return float(max(0.0, psi_val))
    except Exception:
        return 0.0


def detect_distribution_shift(
    current_values: Iterable[float],
    baseline_values: Iterable[float],
    *,
    ratio_threshold: float = 3.0,
    psi_threshold: float = 0.25,
    ks_alpha: float = 0.05,
) -> dict[str, Any]:
    """Robust multi-signal distribution shift detector combining KS-Test, PSI, and Mean Ratio."""
    try:
        cur = np.asarray(list(current_values), dtype=float)
        cur = cur[np.isfinite(cur)]
        base = np.asarray(list(baseline_values), dtype=float)
        base = base[np.isfinite(base)]
    except Exception:
        return {"is_anomaly": False, "score": 0.0, "method": "distribution_shift", "reason": "invalid_input"}

    if cur.size == 0 or base.size == 0:
        return {"is_anomaly": False, "score": 0.0, "method": "distribution_shift", "reason": "empty_input"}

    cur_mean = float(np.mean(cur))
    base_mean = float(np.mean(base))

    # 1. Mean ratio calculation
    if base_mean == 0:
        mean_ratio = float("inf") if cur_mean != 0 else 1.0
    else:
        mean_ratio = max(abs(cur_mean / base_mean), abs(base_mean / cur_mean)) if cur_mean != 0 else float("inf")

    # 2. Two-sample Kolmogorov-Smirnov test
    ks_pvalue = 1.0
    ks_stat = 0.0
    try:
        from scipy.stats import ks_2samp
        ks_res = ks_2samp(cur, base)
        ks_stat = float(ks_res.statistic)
        ks_pvalue = float(ks_res.pvalue)
    except Exception:
        combined = np.sort(np.concatenate([cur, base]))
        cdf1 = np.searchsorted(np.sort(cur), combined, side="right") / cur.size
        cdf2 = np.searchsorted(np.sort(base), combined, side="right") / base.size
        ks_stat = float(np.max(np.abs(cdf1 - cdf2)))
        ks_pvalue = 0.001 if ks_stat > 0.3 else 0.5

    # 3. Population Stability Index (PSI)
    psi_val = _calculate_psi(cur, base)

    # Multi-signal decision
    mean_shift_anomaly = bool(mean_ratio >= ratio_threshold)
    ks_shift_anomaly = bool(ks_pvalue < ks_alpha and ks_stat > 0.4 and (cur.size >= 8 and base.size >= 8))
    psi_shift_anomaly = bool(psi_val >= psi_threshold and (cur.size >= 10 and base.size >= 10))

    is_anomaly = bool(mean_shift_anomaly or ks_shift_anomaly or psi_shift_anomaly)
    score = float(mean_ratio) if mean_shift_anomaly else float(max(ks_stat * 10, psi_val * 10))

    return {
        "is_anomaly": is_anomaly,
        "score": float(score),
        "method": "ks_psi_mean_shift",
        "reason": f"baseline_mean={base_mean:.3f}, current_mean={cur_mean:.3f}, mean_ratio={mean_ratio:.2f}, ks_stat={ks_stat:.3f}, psi={psi_val:.3f}",
        "mean_ratio": float(mean_ratio),
        "ks_stat": float(ks_stat),
        "ks_pvalue": float(ks_pvalue),
        "psi": float(psi_val),
    }


