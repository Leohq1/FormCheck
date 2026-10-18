from evals.system.metrics import completion_rate


def test_completion_rate_counts_terminal_analysis_statuses():
    assert completion_rate(["completed", "queued", "inconclusive"]) == 2 / 3
