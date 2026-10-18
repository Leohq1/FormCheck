from formcheck_biomechanics.models import PhaseName, StrokeWindow
from formcheck_biomechanics.phases import detect_phases
from formcheck_biomechanics.signals import MotionSignals
from synthetic_motion import normalized_wrist_sequence


def _signals(values: list[float]) -> MotionSignals:
    return MotionSignals(
        timestamps_ms=tuple(index * 100 for index in range(len(values))),
        wrist_speed=tuple(values),
        energy=tuple(values),
        version="test",
    )


def test_phases_are_ordered_and_contact_is_a_proxy() -> None:
    sequence = normalized_wrist_sequence([(index * 100, (0.0, float(index))) for index in range(7)])
    result = detect_phases(sequence, StrokeWindow(start_ms=0, end_ms=600, confidence=0.8), _signals([0.2, 0.3, 0.4, 2.0, 0.5, 0.4, 0.3]))

    assert [phase.name for phase in result.phases.phases] == list(PhaseName)
    assert all(0 <= phase.confidence <= 1 and 0 <= phase.uncertainty <= 1 for phase in result.phases.phases)
    contact = result.phases.phases[3]
    assert contact.evidence == ["body_motion_proxy"]
    assert result.phases.contact_available is True


def test_insufficient_follow_through_abstains() -> None:
    sequence = normalized_wrist_sequence([(0, (0.0, 0.0)), (100, (0.0, 1.0))])
    result = detect_phases(
        sequence,
        StrokeWindow(start_ms=0, end_ms=100, confidence=0.5),
        _signals([0.2, 3.0]),
    )
    follow = result.phases.phases[-1]

    assert follow.available is False
    assert follow.unavailable_reason == "insufficient_follow_through"


def test_uncertain_contact_suppresses_contact_without_removing_other_phases() -> None:
    sequence = normalized_wrist_sequence([(index * 100, (0.0, 0.0)) for index in range(5)])
    result = detect_phases(
        sequence,
        StrokeWindow(start_ms=0, end_ms=400, confidence=0.4),
        _signals([1.0, 1.0, 1.0, 1.0, 1.0]),
    )

    assert result.phases.contact_available is False
    assert result.contact_dependent_rules_suppressed is True
    assert result.phases.phases[0].name is PhaseName.PREPARATION
    assert result.phases.phases[0].available is True
