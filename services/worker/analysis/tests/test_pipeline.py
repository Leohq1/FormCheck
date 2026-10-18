from formcheck_analysis.pipeline import analyze_joint_samples
from formcheck_biomechanics.features.arm_extension import JointSample


def test_production_payload_omits_diagnostics_and_findings():
    samples = [
        JointSample(0, 1.0, (0.0, 1.0), (0.0, 0.0), (1.0, 0.0), 0.9),
        JointSample(1, 2.0, (0.0, 1.0), (0.0, 0.0), (1.0, 0.0), 0.9),
    ]

    payload = analyze_joint_samples(samples, analysis_id="abc", diagnostics_enabled=False)

    assert payload["schema_version"] == "0-draft"
    assert payload["findings"] == []
    assert "diagnostics" not in payload


def test_development_payload_keeps_would_trigger_out_of_findings():
    samples = [JointSample(0, 2.0, (0.0, 1.0), (0.0, 0.0), (1.0, 0.0), 0.9)]

    payload = analyze_joint_samples(samples, analysis_id="abc", diagnostics_enabled=True)

    assert payload["findings"] == []
    assert payload["diagnostics"][0]["evaluation"] == "would_trigger"
