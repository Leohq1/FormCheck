from formcheck_biomechanics.features.arm_extension import ArmExtensionFeature
from formcheck_biomechanics.features.base import FeatureRegistry


def build_default_registry() -> FeatureRegistry:
    registry = FeatureRegistry()
    registry.register(ArmExtensionFeature())
    return registry
