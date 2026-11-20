"""Sesión HttpOnly opcional (Bearer sigue válido)."""

from uuid import uuid4

from fastapi.testclient import TestClient

from app.infrastructure.auth_cookie import COOKIE_NAME
from app.main import app, container


def _register_login(client: TestClient) -> tuple[str, object]:
    email = f"cookie-{uuid4()}@example.com"
    password = "Password123!"
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "names": "Cookie",
            "last_names": "Test",
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
    return login.json()["access_token"], login


def test_login_sin_flag_no_setea_cookie() -> None:
    previo = container.settings.auth_cookie_enabled
    container.settings.auth_cookie_enabled = False
    try:
        client = TestClient(app)
        token, login = _register_login(client)
        assert token
        assert COOKIE_NAME not in login.cookies
    finally:
        container.settings.auth_cookie_enabled = previo


def test_login_con_flag_setea_cookie_httponly_y_sirve_sin_bearer() -> None:
    previo = container.settings.auth_cookie_enabled
    container.settings.auth_cookie_enabled = True
    try:
        client = TestClient(app)
        token, login = _register_login(client)
        assert token
        assert COOKIE_NAME in login.cookies
        # Autenticación solo con cookie (sin Authorization); flag sigue activo.
        listed = client.get("/api/v1/contexts")
        assert listed.status_code == 200
    finally:
        container.settings.auth_cookie_enabled = previo


def test_logout_limpia_cookie() -> None:
    previo = container.settings.auth_cookie_enabled
    container.settings.auth_cookie_enabled = True
    try:
        client = TestClient(app)
        _register_login(client)
        assert COOKIE_NAME in client.cookies
        out = client.post("/api/v1/auth/logout")
        assert out.status_code == 200
        listed = client.get("/api/v1/contexts")
        assert listed.status_code == 401
    finally:
        container.settings.auth_cookie_enabled = previo


def test_bearer_sigue_valido_con_cookie_habilitada() -> None:
    previo = container.settings.auth_cookie_enabled
    container.settings.auth_cookie_enabled = True
    try:
        client = TestClient(app)
        token, _ = _register_login(client)
        solo_bearer = TestClient(app)
        listed = solo_bearer.get(
            "/api/v1/contexts",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert listed.status_code == 200
    finally:
        container.settings.auth_cookie_enabled = previo
