"""AI/RAG Observability: Text length shift and embedding norm drift metrics."""
from __future__ import annotations

from typing import Any, Iterable

import numpy as np

from observability.anomaly import zscore_detector


def approximate_token_lengths(texts: Iterable[Any]) -> list[int]:
    """Token length approximation by whitespace splitting with defensive typing."""
    if not texts:
        return []
    lengths = []
    for t in texts:
        if t is None:
            lengths.append(0)
        else:
            lengths.append(len(str(t).strip().split()))
    return lengths


def detect_text_length_shift(
    current_texts: Iterable[str],
    baseline_batch_means: Iterable[float],
    *,
    threshold: float = 3.0,
) -> dict[str, Any]:
    """Detect significant changes in document text length (collapse or explosion)."""
    lengths = approximate_token_lengths(current_texts)
    current_mean = float(np.mean(lengths)) if lengths else 0.0
    result = zscore_detector(current_mean, baseline_batch_means, threshold=threshold)
    result["metric"] = "mean_text_length"
    result["current_mean"] = float(current_mean)
    return result


def detect_embedding_norm_shift(
    current_norms: Iterable[float],
    baseline_norms: Iterable[float],
    *,
    threshold: float = 3.0,
) -> dict[str, Any]:
    """Detect shift in embedding vector norms or cosine similarities."""
    try:
        cur = np.asarray(list(current_norms), dtype=float)
        cur = cur[np.isfinite(cur)]
        base = np.asarray(list(baseline_norms), dtype=float)
        base = base[np.isfinite(base)]
    except Exception:
        return {"is_anomaly": False, "score": 0.0, "method": "embedding_norm_shift", "reason": "invalid_input"}

    if cur.size == 0 or base.size == 0:
        return {"is_anomaly": False, "score": 0.0, "method": "embedding_norm_shift", "reason": "empty_input"}

    cur_mean = float(np.mean(cur))
    base_mean = float(np.mean(base))
    base_std = float(np.std(base))

    if base_std == 0:
        score = float("inf") if cur_mean != base_mean else 0.0
    else:
        score = abs(cur_mean - base_mean) / base_std

    is_anomaly = bool(score > threshold)

    return {
        "is_anomaly": is_anomaly,
        "score": float(score),
        "method": "embedding_norm_zscore",
        "reason": f"base_mean={base_mean:.3f}, cur_mean={cur_mean:.3f}, base_std={base_std:.3f}, threshold={threshold}",
        "current_mean": float(cur_mean),
        "baseline_mean": float(base_mean),
    }


