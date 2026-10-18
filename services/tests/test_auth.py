from formcheck.auth import generate_capability_token, hash_capability_token, tokens_match


def test_token_round_trip():
    token = generate_capability_token()
    digest = hash_capability_token(token)
    assert tokens_match(token, digest)
    assert not tokens_match(token + "x", digest)
