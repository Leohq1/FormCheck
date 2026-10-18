import formcheck_biomechanics.features as features_package
from formcheck_biomechanics.features.arm_extension import ArmExtensionFeature
from formcheck_biomechanics.features.base import FeatureExtractor, FeatureRegistry, FeatureSpec
from formcheck_biomechanics.features.registry import build_default_registry
from formcheck_biomechanics.models import FeatureValue


class _Named:
    def __init__(self, name: str) -> None:
        self.spec = FeatureSpec(
            name=name,
            version="1",
            unit="deg",
            required_landmarks=(),
            supported_views=(),
            handedness_policy="none",
            confidence_strategy="constant",
        )

    def compute(self, context: object) -> FeatureValue:
        del context
        return FeatureValue(name=self.spec.name, available=False, feature_version="1", unavailable_reason="test")


def test_registry_requires_unique_names_and_keeps_deterministic_order() -> None:
    registry = FeatureRegistry()
    registry.register(_Named("beta"))
    registry.register(_Named("alpha"))

    assert [item.name for item in registry.specs] == ["beta", "alpha"]
    try:
        registry.register(_Named("alpha"))
    except ValueError as exc:
        assert "alpha" in str(exc)
    else:
        raise AssertionError("duplicate registration was accepted")


def test_specs_expose_requirements() -> None:
    spec = ArmExtensionFeature().spec

    assert spec.name == "dominant_elbow_angle_at_max_wrist_height_deg"
    assert spec.version == "1"
    assert spec.unit == "deg"
    assert "right_wrist" in spec.required_landmarks
    assert spec.handedness_policy == "canonical_dominant_right"


def test_importing_features_does_not_register_extractors() -> None:
    assert not hasattr(features_package, "build_default_registry")
    fresh = FeatureRegistry()
    assert fresh.specs == ()
    assert build_default_registry().specs[0].name == "dominant_elbow_angle_at_max_wrist_height_deg"


def test_protocol_accepts_the_arm_feature() -> None:
    extractor: FeatureExtractor = ArmExtensionFeature()
    assert extractor.spec.version == "1"
