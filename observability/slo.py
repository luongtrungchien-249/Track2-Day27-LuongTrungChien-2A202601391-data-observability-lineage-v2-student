"""Service Level Objective (SLO), Error Budget, and Multi-Window Burn Rate Alerting."""
from __future__ import annotations

import math
from typing import Any


def calculate_slo(target: float, bad_events: int, total_events: int) -> dict[str, Any]:
    """Calculate SLO compliance, error budget consumption, and burn rate."""
    try:
        t = float(target)
        bad = int(bad_events)
        total = int(total_events)
    except Exception as exc:
        raise ValueError(f"Invalid SLO arguments: {exc}") from exc

    if not 0 < t < 1:
        raise ValueError("target must be strictly between 0 and 1 (exclusive)")
    if bad < 0 or total < 0 or bad > total:
        raise ValueError("invalid event counts: bad_events must be between 0 and total_events")

    allowed_bad_rate = 1.0 - t

    if total == 0:
        return {
            "target": t,
            "actual_bad_rate": 0.0,
            "allowed_bad_rate": allowed_bad_rate,
            "burn_rate": 0.0,
            "remaining_error_budget_fraction": 1.0,
            "breached": False,
        }

    actual_bad_rate = bad / total
    burn_rate = actual_bad_rate / allowed_bad_rate if allowed_bad_rate > 0 else 0.0
    consumed_fraction = actual_bad_rate / allowed_bad_rate if allowed_bad_rate > 0 else 0.0
    remaining_fraction = max(0.0, 1.0 - consumed_fraction)

    return {
        "target": t,
        "actual_bad_rate": float(actual_bad_rate),
        "allowed_bad_rate": float(allowed_bad_rate),
        "burn_rate": float(burn_rate),
        "remaining_error_budget_fraction": float(remaining_fraction),
        "breached": bool(actual_bad_rate > allowed_bad_rate),
    }


def evaluate_multiwindow_burn(
    *,
    short_window_burn: float,
    long_window_burn: float,
    policy: str = "standard",
    fast_burn_threshold: float = 14.0,
    slow_burn_threshold: float = 3.0,
) -> dict[str, Any]:
    """Evaluate multi-window multi-burn-rate policy based on Google SRE standards.

    Paging requires BOTH short and long windows to exceed the burn rate threshold
    to prevent paging on short transient spikes.
    """
    try:
        s_burn = float(short_window_burn) if math.isfinite(float(short_window_burn)) else 0.0
        l_burn = float(long_window_burn) if math.isfinite(float(long_window_burn)) else 0.0
    except Exception:
        s_burn, l_burn = 0.0, 0.0

    s_burn = max(0.0, s_burn)
    l_burn = max(0.0, l_burn)

    # Condition 1: Sustained fast burn (e.g. 14x burn rate over 1h and 6h windows -> 2% budget in 1h)
    if s_burn >= fast_burn_threshold and l_burn >= (fast_burn_threshold * 0.5):
        return {
            "page": True,
            "severity": "critical",
            "reason": f"sustained_fast_burn (short={s_burn:.2f}, long={l_burn:.2f})",
            "short_window_burn": s_burn,
            "long_window_burn": l_burn,
        }

    # Condition 2: General sustained breach (both above 1.0 budget exhaustion rate)
    if s_burn > 1.0 and l_burn > 1.0:
        if s_burn >= slow_burn_threshold and l_burn >= slow_burn_threshold:
            is_critical = bool(s_burn >= 6.0 and l_burn >= 6.0)
            return {
                "page": is_critical,
                "severity": "critical" if is_critical else "warning",
                "reason": f"sustained_burn (short={s_burn:.2f}, long={l_burn:.2f})",
                "short_window_burn": s_burn,
                "long_window_burn": l_burn,
            }
        return {
            "page": False,
            "severity": "warning",
            "reason": f"moderate_burn (short={s_burn:.2f}, long={l_burn:.2f})",
            "short_window_burn": s_burn,
            "long_window_burn": l_burn,
        }

    # Condition 3: Transient spike (short window high, long window normal)
    if s_burn > 1.0 and l_burn <= 1.0:
        return {
            "page": False,
            "severity": "warning" if s_burn >= fast_burn_threshold else "info",
            "reason": f"transient_spike (short={s_burn:.2f}, long={l_burn:.2f})",
            "short_window_burn": s_burn,
            "long_window_burn": l_burn,
        }

    # Condition 4: Healthy
    return {
        "page": False,
        "severity": "info",
        "reason": f"healthy (short={s_burn:.2f}, long={l_burn:.2f})",
        "short_window_burn": s_burn,
        "long_window_burn": l_burn,
    }


