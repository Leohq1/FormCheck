# Video processing

Owner: Person 3.

This package owns ffprobe inspection, analysis-level eligibility checks, FFmpeg normalization, and frame-to-source timestamp mapping. Person 2 owns upload security, object storage, worker orchestration, retries, cancellation, retention, and cleanup.

## Input and storage boundary

The analysis job references the privately stored source upload. This package reads it through Person 2's storage abstraction and writes normalized artifacts through the same abstraction. It must not contain object-store credentials or lifecycle policy.

Logical object names:

```text
analyses/{analysis_id}/source/{filename}
analyses/{analysis_id}/normalized/video.mp4
analyses/{analysis_id}/normalized/timestamps.json
```

## Normalized-video contract

- MP4 with H.264/AVC video and `yuv420p` pixel format.
- Constant 60 fps when the source rate is at least 50 fps; otherwise constant 30 fps.
- Display rotation applied and rotation metadata cleared.
- Audio and non-video streams removed.
- Long edge at most 1920 pixels, aspect ratio preserved, and dimensions even.
- Presentation timestamps start at zero and are monotonic.
- Timestamp JSON maps every output `frame_index` and `normalized_timestamp_ms` to the nearest `source_timestamp_ms`.
- Results record source and output hashes, media metadata, logical object keys, FFmpeg version, and contract version.

Normalization does not claim to create motion detail absent from the source.
