from student_api import detect_distribution


def test_extreme_mean_shift_detected():
    baseline = [9, 10, 11, 10, 10]
    current = [190, 200, 210, 205]
    assert detect_distribution(current, baseline)["is_anomaly"] is True


def test_identical_distributions_no_anomaly():
    baseline = [10.0, 12.0, 11.0, 10.5, 11.5, 10.8]
    current = [10.2, 11.8, 11.1, 10.6, 11.4, 10.9]
    result = detect_distribution(current, baseline)
    assert result["is_anomaly"] is False


def test_empty_distribution_safe():
    assert detect_distribution([], [])["is_anomaly"] is False

