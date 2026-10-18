from evals.generation.metrics import finding_faithfulness, unsupported_claim_rate


def test_faithfulness_rejects_an_invented_finding():
    assert finding_faithfulness(["known", "invented"], {"known"}) == 0.5


def test_unsupported_claim_rate_is_zero_when_every_claim_is_allowed():
    assert unsupported_claim_rate(["extend the arm"], {"extend the arm"}) == 0.0
