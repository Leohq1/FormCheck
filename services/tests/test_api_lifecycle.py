"""API lifecycle / auth / idempotency / cancel tests (no Docker required)."""

from __future__ import annotations

import pytest

CREATE_BODY = {
    "stroke": "overhead_clear",
    "handedness": "right",
    "view_hint": "side",
    "consent": True,
    "filename": "clear.mp4",
    "content_type": "video/mp4",
    "byte_size": 1024,
}


def test_create_rejects_clear_alias(client):
    created = client.post("/api/v1/analyses", json={**CREATE_BODY, "stroke": "clear"})
    assert created.status_code == 400
    assert created.json()["detail"].lower() == "unsupported stroke type"


@pytest.mark.parametrize("stroke", ["smash", "drop"])
def test_create_accepts_smash_and_drop(client, stroke):
    created = client.post("/api/v1/analyses", json={**CREATE_BODY, "stroke": stroke})
    assert created.status_code == 201
    assert created.json()["status"] == "created"


def test_health(client):
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_create_and_get_requires_token(client):
    created = client.post("/api/v1/analyses", json=CREATE_BODY)
    assert created.status_code == 201
    body = created.json()
    analysis_id = body["analysis_id"]
    token = body["capability_token"]

    denied = client.get(f"/api/v1/analyses/{analysis_id}")
    assert denied.status_code in {401, 403, 422}

    ok = client.get(
        f"/api/v1/analyses/{analysis_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert ok.status_code == 200
    assert ok.json()["status"] == "created"


def test_create_idempotency_key_returns_same_analysis(client):
    headers = {"Idempotency-Key": "create-key-1"}
    first = client.post("/api/v1/analyses", json=CREATE_BODY, headers=headers)
    second = client.post("/api/v1/analyses", json=CREATE_BODY, headers=headers)
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["analysis_id"] == second.json()["analysis_id"]
    assert first.json()["capability_token"] == second.json()["capability_token"]


def test_create_idempotency_conflict_on_different_body(client):
    headers = {"Idempotency-Key": "create-key-2"}
    assert client.post("/api/v1/analyses", json=CREATE_BODY, headers=headers).status_code == 201
    other = dict(CREATE_BODY)
    other["byte_size"] = 2048
    conflict = client.post("/api/v1/analyses", json=other, headers=headers)
    assert conflict.status_code == 409


def test_complete_upload_enqueues_job(client, storage_mock):
    created = client.post("/api/v1/analyses", json=CREATE_BODY).json()
    analysis_id = created["analysis_id"]
    token = created["capability_token"]
    res = client.post(
        f"/api/v1/analyses/{analysis_id}/complete-upload",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 202
    assert res.json()["status"] == "queued"
    storage_mock.stat_object.assert_called()


def test_result_not_ready_conflict(client, seeded_analysis):
    analysis, token = seeded_analysis
    res = client.get(
        f"/api/v1/analyses/{analysis.id}/result",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 409


def test_cancel_analysis(client, seeded_analysis):
    analysis, token = seeded_analysis
    res = client.post(
        f"/api/v1/analyses/{analysis.id}/cancel",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 202
    assert res.json()["status"] == "cancelled"

    again = client.post(
        f"/api/v1/analyses/{analysis.id}/cancel",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert again.status_code == 202
    assert again.json()["status"] == "cancelled"


def test_delete_is_idempotent(client, seeded_analysis):
    analysis, token = seeded_analysis
    headers = {
        "Authorization": f"Bearer {token}",
        "Idempotency-Key": "del-key-1",
    }
    first = client.delete(f"/api/v1/analyses/{analysis.id}", headers=headers)
    second = client.delete(f"/api/v1/analyses/{analysis.id}", headers=headers)
    assert first.status_code == 202
    assert second.status_code == 202


@pytest.mark.parametrize("stroke", ["clear", "drive", "net"])
def test_rejects_unsupported_stroke_type(client, stroke):
    body = dict(CREATE_BODY)
    body["stroke"] = stroke
    res = client.post("/api/v1/analyses", json=body)
    assert res.status_code == 400
    assert res.json()["detail"].lower() == "unsupported stroke type"


def test_legacy_shim_environment_cannot_change_result(client, seeded_analysis, db_session, monkeypatch):
    from formcheck.config import get_settings
    from formcheck.worker.fixtures import completed_result, hours_from_now

    monkeypatch.setenv("FORMCHECK_INTERIM_RESULT_SHIM", "1")
    monkeypatch.setenv("INTERIM_RESULT_SHIM", "1")
    get_settings.cache_clear()

    analysis, token = seeded_analysis
    analysis.status = "completed"
    analysis.result_json = completed_result(str(analysis.id), hours_from_now(24))
    db_session.commit()

    res = client.get(
        f"/api/v1/analyses/{analysis.id}/result",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["schema_version"] == "1"
    assert body["feedback"]["tips"]
    assert body["findings"][0]["severity"] == "moderate"
    assert isinstance(body["findings"][0]["evidence"], list)
    assert "recommendations" not in body
    get_settings.cache_clear()


def test_result_returns_ratified_feedback_without_shim(client, seeded_analysis, db_session):
    from formcheck.worker.fixtures import completed_result, hours_from_now

    analysis, token = seeded_analysis
    analysis.status = "completed"
    analysis.result_json = completed_result(str(analysis.id), hours_from_now(24))
    db_session.commit()

    res = client.get(
        f"/api/v1/analyses/{analysis.id}/result",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["schema_version"] == "1"
    assert body["feedback"]["tips"]
    assert body["findings"][0]["severity"] == "moderate"
    assert isinstance(body["findings"][0]["evidence"], list)
    assert "recommendations" not in body


def test_unknown_analysis_is_not_found(client):
    res = client.get(
        "/api/v1/analyses/11111111-1111-4111-8111-111111111111",
        headers={"Authorization": "Bearer deadbeef"},
    )
    assert res.status_code in {401, 404}
