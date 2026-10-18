from formcheck_biomechanics.segmentation import segment_overhead_clear
from synthetic_motion import energy_series


def test_one_dominant_peak_returns_a_window() -> None:
    result = segment_overhead_clear(energy_series([0, 0.1, 0.2, 3.0, 0.2, 0.1, 0]))

    assert result.window is not None
    assert result.competing_candidates == 1
    assert result.window.start_ms <= 300 <= result.window.end_ms


def test_no_candidate_is_inconclusive() -> None:
    result = segment_overhead_clear(energy_series([0.1, 0.1, 0.2, 0.1]))

    assert result.window is None
    assert result.reason == "no_candidate"
    assert result.competing_candidates == 0


def test_candidate_without_surrounding_context_is_inconclusive() -> None:
    result = segment_overhead_clear(energy_series([0.0, 0.1, 0.1, 0.1, 4.0]))

    assert result.window is None
    assert result.reason == "insufficient_context"


def test_two_comparable_peaks_do_not_choose_one() -> None:
    result = segment_overhead_clear(energy_series([0, 0.1, 3.0, 0.1, 2.9, 0.1, 0]))

    assert result.window is None
    assert result.reason == "competing_candidates"
    assert result.competing_candidates == 2
