from __future__ import annotations

import math

from formcheck_pose.models import CANONICAL_LANDMARKS, LandmarkName, PoseLandmark, PoseSequence
from pydantic import BaseModel, ConfigDict, Field

from formcheck_biomechanics.config import DOMINANT_ARM, NormalizationConfig
from formcheck_biomechanics.models import Handedness

_SWAP = {
    LandmarkName.LEFT_EYE_INNER: LandmarkName.RIGHT_EYE_INNER,
    LandmarkName.LEFT_EYE: LandmarkName.RIGHT_EYE,
    LandmarkName.LEFT_EYE_OUTER: LandmarkName.RIGHT_EYE_OUTER,
    LandmarkName.LEFT_EAR: LandmarkName.RIGHT_EAR,
    LandmarkName.MOUTH_LEFT: LandmarkName.MOUTH_RIGHT,
    LandmarkName.LEFT_SHOULDER: LandmarkName.RIGHT_SHOULDER,
    LandmarkName.LEFT_ELBOW: LandmarkName.RIGHT_ELBOW,
    LandmarkName.LEFT_WRIST: LandmarkName.RIGHT_WRIST,
    LandmarkName.LEFT_PINKY: LandmarkName.RIGHT_PINKY,
    LandmarkName.LEFT_INDEX: LandmarkName.RIGHT_INDEX,
    LandmarkName.LEFT_THUMB: LandmarkName.RIGHT_THUMB,
    LandmarkName.LEFT_HIP: LandmarkName.RIGHT_HIP,
    LandmarkName.LEFT_KNEE: LandmarkName.RIGHT_KNEE,
    LandmarkName.LEFT_ANKLE: LandmarkName.RIGHT_ANKLE,
    LandmarkName.LEFT_HEEL: LandmarkName.RIGHT_HEEL,
    LandmarkName.LEFT_FOOT_INDEX: LandmarkName.RIGHT_FOOT_INDEX,
}
_SWAP.update({right: left for left, right in list(_SWAP.items())})


class NormalizedLandmark(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    name: LandmarkName
    available: bool
    x: float | None = Field(default=None, allow_inf_nan=False)
    y: float | None = Field(default=None, allow_inf_nan=False)
    visibility: float | None = Field(default=None, ge=0, le=1, allow_inf_nan=False)
    presence: float | None = Field(default=None, ge=0, le=1, allow_inf_nan=False)
    missing_reason: str | None = None


class NormalizedFrame(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    index: int
    timestamp_ms: int
    landmarks: tuple[NormalizedLandmark, ...]
    scale: float | None = None
    scale_source: str | None = None

    def landmark(self, name: LandmarkName) -> NormalizedLandmark:
        return self.landmarks[list(CANONICAL_LANDMARKS).index(name)]


class NormalizedPoseSequence(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    handedness: Handedness
    frames: tuple[NormalizedFrame, ...]
    version: str


def normalize_pose(
    sequence: PoseSequence,
    handedness: Handedness,
    config: NormalizationConfig | None = None,
) -> NormalizedPoseSequence:
    settings = config or NormalizationConfig()
    frames = tuple(_frame(frame.index, frame.timestamp_ms, frame.landmarks, handedness, settings) for frame in sequence.frames)
    return NormalizedPoseSequence(handedness=handedness, frames=frames, version=settings.version)


def _frame(
    index: int,
    timestamp_ms: int,
    landmarks: tuple[PoseLandmark, ...],
    handedness: Handedness,
    config: NormalizationConfig,
) -> NormalizedFrame:
    by_name = {item.name: item for item in landmarks}
    origin, scale, source = _body_scale(by_name, config)
    normalized: dict[LandmarkName, NormalizedLandmark] = {}
    for name in CANONICAL_LANDMARKS:
        raw = by_name[name]
        point = _point(raw, origin, scale)
        normalized[name] = NormalizedLandmark(
            name=name,
            available=point is not None,
            x=None if point is None else point[0],
            y=None if point is None else point[1],
            visibility=raw.visibility,
            presence=raw.presence,
            missing_reason=None if point is not None else (raw.missing_reason or "scale_unavailable"),
        )
    if handedness is Handedness.LEFT and scale is not None:
        normalized = _mirror(normalized)
    ordered = tuple(normalized[name] for name in CANONICAL_LANDMARKS)
    return NormalizedFrame(
        index=index,
        timestamp_ms=timestamp_ms,
        landmarks=ordered,
        scale=scale,
        scale_source=source,
    )


def _body_scale(
    landmarks: dict[LandmarkName, PoseLandmark],
    config: NormalizationConfig,
) -> tuple[tuple[float, float] | None, float | None, str | None]:
    left_hip = _xy(landmarks[LandmarkName.LEFT_HIP])
    right_hip = _xy(landmarks[LandmarkName.RIGHT_HIP])
    left_shoulder = _xy(landmarks[LandmarkName.LEFT_SHOULDER])
    right_shoulder = _xy(landmarks[LandmarkName.RIGHT_SHOULDER])
    if left_hip is None or right_hip is None:
        return None, None, None
    pelvis = ((left_hip[0] + right_hip[0]) / 2, (left_hip[1] + right_hip[1]) / 2)
    if left_shoulder is not None and right_shoulder is not None:
        shoulder_mid = ((left_shoulder[0] + right_shoulder[0]) / 2, (left_shoulder[1] + right_shoulder[1]) / 2)
        torso = math.dist(shoulder_mid, pelvis)
        if torso >= config.minimum_scale_px:
            return pelvis, torso, "torso_length"
        width = math.dist(left_shoulder, right_shoulder)
        if width >= config.minimum_scale_px:
            return pelvis, width, "shoulder_width"
    return pelvis, None, None


def _point(
    landmark: PoseLandmark,
    origin: tuple[float, float] | None,
    scale: float | None,
) -> tuple[float, float] | None:
    if origin is None or scale is None or not landmark.available or landmark.x is None or landmark.y is None:
        return None
    return ((landmark.x - origin[0]) / scale, (origin[1] - landmark.y) / scale)


def _mirror(landmarks: dict[LandmarkName, NormalizedLandmark]) -> dict[LandmarkName, NormalizedLandmark]:
    mirrored: dict[LandmarkName, NormalizedLandmark] = {}
    for name in CANONICAL_LANDMARKS:
        source_name = _SWAP.get(name, name)
        source = landmarks[source_name]
        mirrored[name] = source.model_copy(
            update={
                "name": name,
                "x": None if source.x is None else -source.x,
            }
        )
    return mirrored


def _xy(landmark: PoseLandmark) -> tuple[float, float] | None:
    if not landmark.available or landmark.x is None or landmark.y is None:
        return None
    return (landmark.x, landmark.y)


def dominant_names(handedness: Handedness) -> tuple[LandmarkName, LandmarkName, LandmarkName]:
    return DOMINANT_ARM[handedness]
