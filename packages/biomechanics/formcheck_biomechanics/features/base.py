from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from formcheck_biomechanics.models import FeatureValue, StrokeWindow, ViewHint
from formcheck_biomechanics.normalization import NormalizedPoseSequence


@dataclass(frozen=True)
class FeatureSpec:
    name: str
    version: str
    unit: str
    required_landmarks: tuple[str, ...]
    supported_views: tuple[ViewHint, ...]
    handedness_policy: str
    confidence_strategy: str


@dataclass(frozen=True)
class FeatureContext:
    sequence: NormalizedPoseSequence
    window: StrokeWindow | None
    view: ViewHint | None


class FeatureExtractor(Protocol):
    spec: FeatureSpec

    def compute(self, context: FeatureContext) -> FeatureValue: ...


class FeatureRegistry:
    def __init__(self) -> None:
        self._extractors: list[FeatureExtractor] = []

    def register(self, extractor: FeatureExtractor) -> None:
        key = (extractor.spec.name, extractor.spec.version)
        if any((item.spec.name, item.spec.version) == key for item in self._extractors):
            raise ValueError(f"duplicate feature registration: {key}")
        self._extractors.append(extractor)

    def extract_all(self, context: FeatureContext) -> tuple[FeatureValue, ...]:
        ordered = sorted(self._extractors, key=lambda item: (item.spec.name, item.spec.version))
        return tuple(item.compute(context) for item in ordered)

    @property
    def specs(self) -> tuple[FeatureSpec, ...]:
        return tuple(item.spec for item in self._extractors)
