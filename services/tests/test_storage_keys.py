from formcheck.storage import source_object_key, rewrite_presign_host_for_browser


def test_source_object_key_sanitizes_path():
    key = source_object_key("abc", "../../evil.mp4")
    assert key == "analyses/abc/source/evil.mp4"


def test_presign_host_rewrite():
    url = "http://minio:9000/formcheck/analyses/x/source/a.mp4?X-Amz-Signature=1"
    rewritten = rewrite_presign_host_for_browser(url, "http://localhost:9000")
    assert rewritten.startswith("http://localhost:9000/")
