from formcheck.idempotency import hash_request_body


def test_request_hash_is_stable():
    a = hash_request_body({"stroke": "overhead_clear", "consent": True})
    b = hash_request_body({"consent": True, "stroke": "overhead_clear"})
    assert a == b


def test_request_hash_changes_with_body():
    a = hash_request_body({"byte_size": 1})
    b = hash_request_body({"byte_size": 2})
    assert a != b
