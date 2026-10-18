from __future__ import annotations

from enum import Enum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class LandmarkName(str, Enum):
    NOSE = "nose"
    LEFT_EYE_INNER = "left_eye_inner"
    LEFT_EYE = "left_eye"
    LEFT_EYE_OUTER = "left_eye_outer"
    RIGHT_EYE_INNER = "right_eye_inner"
    RIGHT_EYE = "right_eye"
    RIGHT_EYE_OUTER = "right_eye_outer"
    LEFT_EAR = "left_ear"
    RIGHT_EAR = "right_ear"
    MOUTH_LEFT = "mouth_left"
    MOUTH_RIGHT = "mouth_right"
    LEFT_SHOULDER = "left_shoulder"
    RIGHT_SHOULDER = "right_shoulder"
    LEFT_ELBOW = "left_elbow"
    RIGHT_ELBOW = "right_elbow"
    LEFT_WRIST = "left_wrist"
    RIGHT_WRIST = "right_wrist"
    LEFT_PINKY = "left_pinky"
    RIGHT_PINKY = "right_pinky"
    LEFT_INDEX = "left_index"
    RIGHT_INDEX = "right_index"
    LEFT_THUMB = "left_thumb"
    RIGHT_THUMB = "right_thumb"
    LEFT_HIP = "left_hip"
    RIGHT_HIP = "right_hip"
    LEFT_KNEE = "left_knee"
    RIGHT_KNEE = "right_knee"
    LEFT_ANKLE = "left_ankle"
    RIGHT_ANKLE = "right_ankle"
    LEFT_HEEL = "left_heel"
    RIGHT_HEEL = "right_heel"
    LEFT_FOOT_INDEX = "left_foot_index"
    RIGHT_FOOT_INDEX = "right_foot_index"


CANONICAL_LANDMARKS: tuple[LandmarkName, ...] = tuple(LandmarkName)


class PoseLandmark(BaseModel):
    """One canonical landmark. ``relative_z`` is the estimator's non-metric depth."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: LandmarkName
    available: bool
    x: float | None = Field(default=None, allow_inf_nan=False)
    y: float | None = Field(default=None, allow_inf_nan=False)
    relative_z: float | None = Field(default=None, allow_inf_nan=False)
    visibility: float | None = Field(default=None, ge=0, le=1, allow_inf_nan=False)
    presence: float | None = Field(default=None, ge=0, le=1, allow_inf_nan=False)
    missing_reason: str | None = None

    @model_validator(mode="after")
    def availability_matches_coordinates(self) -> Self:
        if self.available:
            if self.x is None or self.y is None:
                raise ValueError("available landmark requires finite x and y")
            if self.missing_reason is not None:
                raise ValueError("available landmark cannot have a missing reason")
        elif self.x is not None or self.y is not None or self.relative_z is not None:
            raise ValueError("unavailable landmark cannot have coordinates")
        elif not self.missing_reason:
            raise ValueError("unavailable landmark requires a missing reason")
        return self


class PoseFrame(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    index: int = Field(ge=0)
    timestamp_ms: int = Field(ge=0)
    detected_pose_count: int = Field(ge=0)
    landmarks: tuple[PoseLandmark, ...]

    @model_validator(mode="after")
    def landmarks_follow_canonical_order(self) -> Self:
        names = tuple(item.name for item in self.landmarks)
        if names != CANONICAL_LANDMARKS:
            raise ValueError("landmarks must include every canonical name in canonical order")
        return self

    def landmark(self, name: LandmarkName) -> PoseLandmark:
        return self.landmarks[CANONICAL_LANDMARKS.index(name)]


class PoseSequence(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: str = "pose.v1"
    estimator_name: str
    estimator_version: str
    model_version: str
    frames: tuple[PoseFrame, ...]

    @model_validator(mode="after")
    def timestamps_are_strictly_increasing(self) -> Self:
        previous: int | None = None
        for frame in self.frames:
            if previous is not None and frame.timestamp_ms <= previous:
                raise ValueError("pose timestamps must be strictly increasing")
            previous = frame.timestamp_ms
        return self
