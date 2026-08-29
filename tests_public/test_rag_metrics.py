from student_api import rag_embedding_shift, rag_length_shift


def test_rag_length_collapse_is_detected():
    baseline_batch_means = [40, 42, 39, 41, 43, 40, 42]
    current_texts = ["x y", "a b c", "one two"]
    assert rag_length_shift(current_texts, baseline_batch_means)["is_anomaly"] is True


def test_rag_embedding_shift_is_detected():
    baseline_norms = [1.0, 1.02, 0.98, 1.01, 0.99, 1.0]
    current_norms = [2.5, 2.6, 2.4, 2.7]
    assert rag_embedding_shift(current_norms, baseline_norms)["is_anomaly"] is True


def test_rag_length_normal_is_not_anomaly():
    baseline_batch_means = [40, 42, 39, 41, 43, 40, 42]
    current_texts = ["word " * 41 for _ in range(5)]
    assert rag_length_shift(current_texts, baseline_batch_means)["is_anomaly"] is False


def test_rag_empty_inputs_do_not_crash():
    res_len = rag_length_shift([], [40, 42, 41, 40, 42])
    assert res_len["is_anomaly"] is True  # 0 length vs 41 baseline is anomaly
    res_emb = rag_embedding_shift([], [])
    assert res_emb["is_anomaly"] is False



