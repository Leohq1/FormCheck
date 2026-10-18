from formcheck_biomechanics.models import ViewHint

from formcheck_rules.definitions import RuleDefinition
from formcheck_rules.models import CalibrationStatus

LOW_ARM_EXTENSION_RULE_ID = "clear.low_arm_extension.v1"
PROVISIONAL_TEST_ONLY = "provisional_test_only"
DEVELOPMENT_LOW_ARM_EXTENSION_THRESHOLD_DEG = 140.0

LOW_ARM_EXTENSION = RuleDefinition(
    rule_id=LOW_ARM_EXTENSION_RULE_ID,
    enabled=False,
    calibration_status=CalibrationStatus.NOT_CALIBRATED,
    required_feature="dominant_elbow_angle_at_max_wrist_height_deg",
    supported_views=(ViewHint.SIDE, ViewHint.REAR_THREE_QUARTER),
    minimum_confidence=0.5,
    operator=None,
    threshold=None,
    severity=None,
    label="Low arm extension",
    retrieval_tags=("overhead_clear", "arm_extension"),
)

PRODUCTION_CATALOG: tuple[RuleDefinition, ...] = (LOW_ARM_EXTENSION,)
