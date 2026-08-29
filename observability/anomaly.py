"""Anomaly detection module with robust statistical methods, EWMA, and context awareness."""
from __future__ import annotations

from typing import Any, Iterable

import numpy as np


def _clean_numeric_array(data: Iterable[Any]) -> np.ndarray:
    try:
        arr = np.asarray(list(data), dtype=float)
        return arr[np.isfinite(arr)]
    except Exception:
        return np.array([], dtype=float)


def zscore_detector(current: float, history: Iterable[float], threshold: float = 3.0) -> dict[str, Any]:
    values = _clean_numeric_array(history)
    if values.size < 3:
        return {"is_anomaly": False, "score": 0.0, "method": "zscore", "reason": "insufficient_history"}
    mean = float(np.mean(values))
    std = float(np.std(values))
    cur = float(current)
    if std == 0:
        score = float("inf") if cur != mean else 0.0
    else:
        score = abs(cur - mean) / std
    return {
        "is_anomaly": bool(score > threshold),
        "score": float(score),
        "method": "zscore",
        "reason": f"mean={mean:.3f}, std={std:.3f}, threshold={threshold}",
    }


def mad_detector(current: float, history: Iterable[float], threshold: float = 3.5) -> dict[str, Any]:
    """Robust Median Absolute Deviation detector with zero-MAD edge case handling."""
    values = _clean_numeric_array(history)
    if values.size < 3:
        return {"is_anomaly": False, "score": 0.0, "method": "mad", "reason": "insufficient_history"}
    median = float(np.median(values))
    mad = float(np.median(np.abs(values - median)))
    cur = float(current)
    if mad == 0:
        std = float(np.std(values))
        if cur == median:
            score = 0.0
        elif std > 0:
            score = abs(cur - median) / std
        else:
            score = float("inf")
        return {
            "is_anomaly": bool(score > threshold),
            "score": float(score),
            "method": "mad",
            "reason": f"mad_is_zero; fallback_std={std:.3f}, median={median:.3f}, threshold={threshold}",
        }
    modified_z = 0.6745 * abs(cur - median) / mad
    return {
        "is_anomaly": bool(modified_z > threshold),
        "score": float(modified_z),
        "method": "mad",
        "reason": f"median={median:.3f}, mad={mad:.3f}, threshold={threshold}",
    }


def ewma_detector(current: float, history: Iterable[float], span: int = 7, threshold: float = 3.0) -> dict[str, Any]:
    """Exponential Weighted Moving Average (EWMA) anomaly detector."""
    values = _clean_numeric_array(history)
    if values.size < 3:
        return {"is_anomaly": False, "score": 0.0, "method": "ewma", "reason": "insufficient_history"}
    alpha = 2.0 / (span + 1.0)
    weights = (1.0 - alpha) ** np.arange(len(values) - 1, -1, -1)
    weights /= weights.sum()
    ewma_mean = float(np.sum(weights * values))
    ewma_std = float(np.sqrt(np.sum(weights * (values - ewma_mean) ** 2)))
    cur = float(current)
    if ewma_std == 0:
        score = float("inf") if cur != ewma_mean else 0.0
    else:
        score = abs(cur - ewma_mean) / ewma_std
    return {
        "is_anomaly": bool(score > threshold),
        "score": float(score),
        "method": "ewma",
        "reason": f"ewma_mean={ewma_mean:.3f}, ewma_std={ewma_std:.3f}, threshold={threshold}",
    }


def detect_anomaly(
    current: float,
    history: Iterable[float],
    *,
    method: str = "auto",
    threshold: float = 3.0,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Context-aware anomaly detector supporting zscore, mad, ewma, and auto modes."""
    if method == "mad":
        return mad_detector(current, history, threshold=threshold)
    if method == "zscore":
        return zscore_detector(current, history, threshold=threshold)
    if method == "ewma":
        return ewma_detector(current, history, threshold=threshold)
    if method == "auto":
        effective_history = list(history)
        context_applied = []

        if context:
            if "same_segment_history" in context and context["same_segment_history"]:
                seg_hist = list(context["same_segment_history"])
                if len(seg_hist) >= 3:
                    effective_history = seg_hist
                    context_applied.append("same_segment_history")
            elif "seasonal_history" in context and context["seasonal_history"]:
                season_hist = list(context["seasonal_history"])
                if len(season_hist) >= 3:
                    effective_history = season_hist
                    context_applied.append("seasonal_history")
            elif "same_dow_history" in context and context["same_dow_history"]:
                dow_hist = list(context["same_dow_history"])
                if len(dow_hist) >= 3:
                    effective_history = dow_hist
                    context_applied.append("same_dow_history")

        values = _clean_numeric_array(effective_history)
        if values.size < 3:
            return {
                "is_anomaly": False,
                "score": 0.0,
                "method": "auto:insufficient_history",
                "reason": "insufficient_history",
            }

        # Select MAD when sample size >= 5 for outlier resistance; fallback to Z-score
        if values.size >= 5:
            res = mad_detector(current, values, threshold=threshold)
            chosen_method = "auto:mad"
        else:
            res = zscore_detector(current, values, threshold=threshold)
            chosen_method = "auto:zscore"

        res["method"] = chosen_method
        if context_applied:
            res["reason"] += f"; context_applied={','.join(context_applied)}"
        return res

    raise ValueError(f"Unsupported method: {method}")


