from formcheck_biomechanics.signals import compute_motion_signals
from synthetic_motion import normalized_wrist_sequence


def test_velocity_uses_elapsed_time_instead_of_frame_index() -> None:
    slow = compute_motion_signals(normalized_wrist_sequence([(0, (0.0, 0.0)), (1000, (1.0, 0.0))]))
    fast = compute_motion_signals(normalized_wrist_sequence([(0, (0.0, 0.0)), (500, (1.0, 0.0))]))

    assert slow.wrist_speed[1] is not None and fast.wrist_speed[1] is not None
    assert fast.wrist_speed[1] > slow.wrist_speed[1] * 1.5


def test_missing_samples_remain_gaps() -> None:
    signals = compute_motion_signals(
        normalized_wrist_sequence([(0, (0.0, 0.0)), (50, None), (100, (1.0, 0.0))])
    )

    assert signals.wrist_speed[1] is None
    assert signals.energy[1] is None


def test_smoothing_does_not_cross_a_long_occlusion() -> None:
    signals = compute_motion_signals(
        normalized_wrist_sequence(
            [
                (0, (0.0, 0.0)),
                (40, (0.1, 0.0)),
                (80, (0.2, 0.0)),
                (400, (0.2, 0.0)),
                (440, (4.0, 0.0)),
            ]
        )
    )

    assert signals.energy[2] is not None and signals.energy[4] is not None
    assert signals.energy[2] < 5
    assert signals.energy[4] > signals.energy[2]


def test_constant_pose_has_near_zero_energy() -> None:
    signals = compute_motion_signals(
        normalized_wrist_sequence([(0, (1.0, 1.0)), (40, (1.0, 1.0)), (80, (1.0, 1.0))])
    )

    assert signals.energy[1] == 0
    assert signals.energy[2] == 0
