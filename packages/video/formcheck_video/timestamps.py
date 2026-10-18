from __future__ import annotations

import bisect
from collections.abc import Sequence

from formcheck_video.models import TimestampMapEntry


def map_output_to_source(
    output_timestamps_ms: Sequence[int],
    source_pts_ms: Sequence[int],
) -> tuple[TimestampMapEntry, ...]:
    if not source_pts_ms:
        raise ValueError("source presentation timestamps are required")
    ordered = tuple(sorted(source_pts_ms))
    entries: list[TimestampMapEntry] = []
    for index, timestamp in enumerate(output_timestamps_ms):
        entries.append(
            TimestampMapEntry(
                frame_index=index,
                normalized_timestamp_ms=timestamp,
                source_timestamp_ms=_nearest_earlier(ordered, timestamp),
            )
        )
    return tuple(entries)


def _nearest_earlier(source_pts_ms: Sequence[int], timestamp: int) -> int:
    insert_at = bisect.bisect_left(source_pts_ms, timestamp)
    if insert_at <= 0:
        return source_pts_ms[0]
    if insert_at >= len(source_pts_ms):
        return source_pts_ms[-1]
    before = source_pts_ms[insert_at - 1]
    after = source_pts_ms[insert_at]
    if abs(timestamp - before) <= abs(after - timestamp):
        return before
    return after
