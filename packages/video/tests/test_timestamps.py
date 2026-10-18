from formcheck_video.timestamps import map_output_to_source
from hypothesis import given
from hypothesis import strategies as st


def test_exact_tie_selects_the_earlier_source_timestamp() -> None:
    mapped = map_output_to_source([10], [0, 20])

    assert mapped[0].source_timestamp_ms == 0
    assert mapped[0].normalized_timestamp_ms == 10


def test_duplicate_output_frames_may_share_a_source_timestamp() -> None:
    mapped = map_output_to_source([0, 10], [0, 100])

    assert mapped[0].source_timestamp_ms == mapped[1].source_timestamp_ms == 0


def test_dropped_source_timestamps_leave_gaps() -> None:
    mapped = map_output_to_source([0, 100], [0, 40, 100])

    used = {entry.source_timestamp_ms for entry in mapped}
    assert 40 not in used
    assert [entry.normalized_timestamp_ms for entry in mapped] == [0, 100]


@given(
    source=st.lists(st.integers(min_value=0, max_value=20_000), min_size=1, max_size=12, unique=True).map(sorted),
    start=st.integers(min_value=0, max_value=200),
    step=st.integers(min_value=1, max_value=80),
    count=st.integers(min_value=1, max_value=16),
)
def test_constant_rate_output_maps_to_nearest_source_monotonic(
    source: list[int],
    start: int,
    step: int,
    count: int,
) -> None:
    output = [start + (index * step) for index in range(count)]
    mapped = map_output_to_source(output, source)

    assert [entry.normalized_timestamp_ms for entry in mapped] == output
    assert [entry.frame_index for entry in mapped] == list(range(count))
    for entry, timestamp in zip(mapped, output, strict=True):
        nearest = min(source, key=lambda item: (abs(item - timestamp), item))
        assert entry.source_timestamp_ms == nearest
