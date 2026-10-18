import pytest
from formcheck_biomechanics.models import FeatureValue
from pydantic import ValidationError


def test_confidence_is_unit_interval() -> None:
    with pytest.raises(ValidationError):
        FeatureValue(
            name="dominant_elbow_angle_at_max_wrist_height_deg",
            value=90.0,
            unit="deg",
            confidence=1.1,
            available=True,
            feature_version="1",
        )


def test_unavailable_feature_has_no_value() -> None:
    feature = FeatureValue(
        name="dominant_elbow_angle_at_max_wrist_height_deg",
        available=False,
        feature_version="1",
        unavailable_reason="missing_landmark",
    )

    assert feature.value is None
    assert feature.unit is None


def test_unavailable_feature_rejects_a_numeric_value() -> None:
    with pytest.raises(ValidationError, match="unavailable"):
        FeatureValue(
            name="dominant_elbow_angle_at_max_wrist_height_deg",
            value=90.0,
            unit="deg",
            available=False,
            feature_version="1",
            unavailable_reason="missing_landmark",
        )


def test_available_feature_requires_value_unit_and_version() -> None:
    with pytest.raises(ValidationError):
        FeatureValue(
            name="dominant_elbow_angle_at_max_wrist_height_deg",
            available=True,
            feature_version="1",
        )
