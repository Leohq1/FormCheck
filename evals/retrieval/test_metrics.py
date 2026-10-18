from evals.retrieval.metrics import citation_validity, recall_at_k


def test_recall_at_five_counts_a_relevant_hit():
    score = recall_at_k(["a", "b", "c"], {"b"}, k=5)
    assert score == 1.0


def test_citation_validity_rejects_an_unknown_chunk():
    score = citation_validity([("source", "chunk"), ("other", "missing")], {("source", "chunk")})
    assert score == 0.5
