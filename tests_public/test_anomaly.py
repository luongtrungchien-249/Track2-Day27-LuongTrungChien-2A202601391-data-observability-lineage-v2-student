from student_api import detect_metric


def test_large_volume_drop_is_anomaly():
    history = [1000, 1010, 995, 1008, 1004, 1012, 998]
    result = detect_metric(300, history, method="zscore")
    assert result["is_anomaly"] is True


def test_stable_value_is_not_anomaly():
    history = [1000, 1010, 995, 1008, 1004, 1012, 998]
    result = detect_metric(1002, history, method="zscore")
    assert result["is_anomaly"] is False


def test_mad_detector_handles_outliers():
    history = [100, 100, 100, 100, 100, 500]  # Skewed with outlier
    result = detect_metric(100, history, method="mad")
    assert result["is_anomaly"] is False


def test_auto_detector_uses_context_segment():
    weekday_history = [200, 205, 198, 202, 201]
    weekend_history = [50, 52, 49, 51, 48]
    # Current value 50 would be anomaly for weekday history, but matches weekend history
    result = detect_metric(
        50,
        weekday_history,
        method="auto",
        context={"same_segment_history": weekend_history},
    )
    assert result["is_anomaly"] is False


def test_zero_mad_detects_deviation():
    constant_history = [10.0, 10.0, 10.0, 10.0, 10.0]
    result = detect_metric(50.0, constant_history, method="mad")
    assert result["is_anomaly"] is True


def test_insufficient_history_returns_safe():
    small_history = [10.0]
    result = detect_metric(10.0, small_history, method="auto")
    assert result["is_anomaly"] is False
    assert result["score"] == 0.0


def test_generator_history_support():
    gen = (x for x in [100, 102, 98, 101, 99])
    result = detect_metric(100, gen, method="zscore")
    assert result["is_anomaly"] is False


