from __future__ import annotations

from formcheck_video.models import VideoEligibility, VideoInspection

MAX_BYTES = 100 * 1024 * 1024
MAX_SECONDS = 30.0
MIN_FPS = 30.0
MAX_FPS = 120.0
MIN_SHORT_EDGE = 720

_ACCEPTED = {"mp4", "mov"}
_REMEDIATION = {
    "VIDEO_UNSUPPORTED_CONTAINER": "Upload an MP4 or MOV file.",
    "VIDEO_TOO_LARGE": "Upload a video of at most 100 MB.",
    "VIDEO_TOO_LONG": "Upload a video of at most 30 seconds.",
    "VIDEO_FPS_UNSUPPORTED": "Record between 30 and 120 frames per second.",
    "VIDEO_DECODE_FAILED": "The video could not be decoded. Export it again as MP4 or MOV.",
    "VIDEO_LOW_RESOLUTION": "720p or higher is recommended.",
}


def assess_eligibility(inspection: VideoInspection) -> VideoEligibility:
    codes: list[str] = []
    warnings: list[str] = []
    if inspection.container not in _ACCEPTED:
        codes.append("VIDEO_UNSUPPORTED_CONTAINER")
    if inspection.byte_size > MAX_BYTES:
        codes.append("VIDEO_TOO_LARGE")
    if inspection.duration_seconds > MAX_SECONDS:
        codes.append("VIDEO_TOO_LONG")
    if not inspection.decode_ok:
        codes.append("VIDEO_DECODE_FAILED")
    fps = inspection.average_fps if inspection.average_fps is not None else inspection.nominal_fps
    if fps is None or fps < MIN_FPS or fps > MAX_FPS:
        codes.append("VIDEO_FPS_UNSUPPORTED")
    short_edge = min(inspection.width, inspection.height)
    if short_edge < MIN_SHORT_EDGE:
        warnings.append("VIDEO_LOW_RESOLUTION")
    labels = codes + warnings
    return VideoEligibility(
        eligible=not codes,
        codes=codes,
        warnings=warnings,
        remediation=[_REMEDIATION[code] for code in labels],
    )
