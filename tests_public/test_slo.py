import pytest
from student_api import multiwindow_burn, slo_status


def test_burn_rate_math():
    result = slo_status(0.995, bad_events=2, total_events=100)
    assert result["allowed_bad_rate"] == pytest.approx(0.005)
    assert result["actual_bad_rate"] == pytest.approx(0.02)
    assert result["burn_rate"] == pytest.approx(4.0)
    assert result["breached"] is True


def test_zero_events_is_safe():
    result = slo_status(0.99, bad_events=0, total_events=0)
    assert result["burn_rate"] == 0
    assert result["breached"] is False


def test_multiwindow_sustained_fast_burn_pages():
    res = multiwindow_burn(short_window_burn=15.0, long_window_burn=14.0)
    assert res["page"] is True
    assert res["severity"] == "critical"


def test_multiwindow_transient_spike_does_not_page():
    res = multiwindow_burn(short_window_burn=15.0, long_window_burn=0.5)
    assert res["page"] is False


def test_slo_invalid_target_raises_value_error():
    with pytest.raises(ValueError):
        slo_status(1.5, bad_events=0, total_events=100)
    with pytest.raises(ValueError):
        slo_status(-0.5, bad_events=0, total_events=100)


def test_slo_invalid_event_counts_raises_value_error():
    with pytest.raises(ValueError):
        slo_status(0.99, bad_events=150, total_events=100)
    with pytest.raises(ValueError):
        slo_status(0.99, bad_events=-1, total_events=100)


def test_slo_perfect_compliance():
    res = slo_status(0.999, bad_events=0, total_events=1000)
    assert res["actual_bad_rate"] == 0.0
    assert res["burn_rate"] == 0.0
    assert res["remaining_error_budget_fraction"] == 1.0
    assert res["breached"] is False


