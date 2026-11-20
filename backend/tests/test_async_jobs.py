"""Endpoints async de indexación / consulta + GET /jobs/{id}."""

from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app, container

client = TestClient(app)


def _auth_headers() -> dict[str, str]:
    email = f"jobs-{uuid4()}@example.com"
    password = "Password123!"
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "names": "Jobs",
            "last_names": "Queue",
            "email": email,
            "password": password,
        },
    )
    assert reg.status_code == 201, reg.text
    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_index_async_acepta_y_consulta_estado() -> None:
    previo = container.settings.async_jobs_enabled
    container.settings.async_jobs_enabled = True
    try:
        headers = _auth_headers()
        accepted = client.post("/api/v1/knowledge/index/async", headers=headers)
        assert accepted.status_code == 202, accepted.text
        body = accepted.json()
        assert body["job_type"] == "knowledge_index"
        assert body["job_id"]
        job = client.get(f"/api/v1/jobs/{body['job_id']}", headers=headers)
        assert job.status_code == 200
        assert job.json()["id"] == body["job_id"]
        assert job.json()["status"] in {"queued", "running", "completed", "failed"}
    finally:
        container.settings.async_jobs_enabled = previo


def test_query_async_requiere_contexto() -> None:
    previo = container.settings.async_jobs_enabled
    container.settings.async_jobs_enabled = True
    try:
        headers = _auth_headers()
        accepted = client.post(
            "/api/v1/queries/async",
            headers=headers,
            json={"text": "¿Cómo riego la papa?"},
        )
        assert accepted.status_code == 202, accepted.text
        job_id = accepted.json()["job_id"]
        # Sin contexto el worker falla; el job debe terminar en failed.
        import time

        deadline = time.time() + 5.0
        status = "queued"
        while time.time() < deadline:
            job = client.get(f"/api/v1/jobs/{job_id}", headers=headers)
            assert job.status_code == 200
            status = job.json()["status"]
            if status in {"completed", "failed"}:
                break
            time.sleep(0.1)
        assert status == "failed"
        assert job.json().get("error")
    finally:
        container.settings.async_jobs_enabled = previo


def test_async_deshabilitado_devuelve_503() -> None:
    previo = container.settings.async_jobs_enabled
    container.settings.async_jobs_enabled = False
    try:
        headers = _auth_headers()
        r = client.post("/api/v1/knowledge/index/async", headers=headers)
        assert r.status_code == 503
    finally:
        container.settings.async_jobs_enabled = previo


def test_job_ajeno_devuelve_403() -> None:
    previo = container.settings.async_jobs_enabled
    container.settings.async_jobs_enabled = True
    try:
        headers_a = _auth_headers()
        accepted = client.post("/api/v1/knowledge/index/async", headers=headers_a)
        assert accepted.status_code == 202
        job_id = accepted.json()["job_id"]
        headers_b = _auth_headers()
        denied = client.get(f"/api/v1/jobs/{job_id}", headers=headers_b)
        assert denied.status_code == 403
    finally:
        container.settings.async_jobs_enabled = previo
