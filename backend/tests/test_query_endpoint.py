from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.infrastructure.adapters.output.mysql.connection import create_mysql_engine
from app.main import app, container

client = TestClient(app)
REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
CONTEXTS_URL = "/api/v1/contexts"
QUERIES_URL = "/api/v1/queries"
QUESTION = "¿Qué puedo hacer para mejorar el cultivo de papa?"


def _register_and_login(email: str | None = None) -> dict[str, str]:
    payload = {
        "names": "Ana",
        "last_names": "Huaman",
        "email": email or f"hu04-{uuid4()}@example.com",
        "password": "Password123!",
    }
    register = client.post(REGISTER_URL, json=payload)
    assert register.status_code == 201
    login = client.post(
        LOGIN_URL,
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert login.status_code == 200
    return {
        "email": payload["email"],
        "token": login.json()["access_token"],
        "farmer_id": login.json()["farmer"]["id"],
    }


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create_and_select_context(token: str, crop: str = "papa", region: str = "Huancayo") -> dict:
    created = client.post(
        CONTEXTS_URL,
        json={
            "plot_name": "Parcela 1",
            "crop": crop,
            "region": region,
            "notes": "Campana seca",
        },
        headers=_auth(token),
    )
    assert created.status_code == 201
    selected = client.post(
        f"{CONTEXTS_URL}/{created.json()['id']}/select",
        headers=_auth(token),
    )
    assert selected.status_code == 200
    return selected.json()


def test_submit_query_requires_auth() -> None:
    response = client.post(QUERIES_URL, json={"text": QUESTION})
    assert response.status_code == 401


def test_submit_query_rejects_invalid_token() -> None:
    response = client.post(
        QUERIES_URL,
        json={"text": QUESTION},
        headers=_auth("token-invalido"),
    )
    assert response.status_code == 401


def test_submit_query_rejects_expired_token() -> None:
    user = _register_and_login()
    expired = jwt.encode(
        {
            "sub": user["farmer_id"],
            "email": user["email"],
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        },
        container.settings.jwt_secret,
        algorithm=container.settings.jwt_algorithm,
    )
    response = client.post(
        QUERIES_URL,
        json={"text": QUESTION},
        headers=_auth(expired),
    )
    assert response.status_code == 401


def test_submit_query_empty_text_returns_422() -> None:
    user = _register_and_login()
    response = client.post(
        QUERIES_URL,
        json={"text": ""},
        headers=_auth(user["token"]),
    )
    assert response.status_code == 422


def test_submit_query_without_selected_context_returns_controlled_error() -> None:
    user = _register_and_login()
    response = client.post(
        QUERIES_URL,
        json={"text": QUESTION},
        headers=_auth(user["token"]),
    )
    assert response.status_code == 409
    assert "contexto" in response.json()["detail"].lower()


def test_submit_query_success_returns_query_and_template_answer() -> None:
    user = _register_and_login()
    context = _create_and_select_context(user["token"])
    response = client.post(
        QUERIES_URL,
        json={"text": QUESTION},
        headers=_auth(user["token"]),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["id"]
    assert body["text"] == QUESTION
    assert body["answer"]
    assert body["generation_method"] == "template"
    assert "papa" in body["answer"]
    assert "Huancayo" in body["answer"]
    assert body["context"]["id"] == context["id"]
    assert body["context"]["crop"] == "papa"
    assert body["context"]["region"] == "Huancayo"
    assert body["created_at"]
    serialized = str(body)
    assert "password" not in serialized
    assert "password_hash" not in serialized
    assert user["token"] not in serialized


def test_submit_query_ignores_forged_farmer_id() -> None:
    user = _register_and_login()
    context = _create_and_select_context(user["token"])
    other_id = str(uuid4())
    response = client.post(
        QUERIES_URL,
        json={"text": QUESTION, "farmer_id": other_id},
        headers=_auth(user["token"]),
    )
    assert response.status_code == 201
    assert response.json()["context"]["id"] == context["id"]
    assert other_id not in str(response.json())


def test_submit_query_does_not_use_another_farmer_context() -> None:
    farmer_a = _register_and_login()
    farmer_b = _register_and_login()
    context_b = _create_and_select_context(farmer_b["token"], crop="maiz", region="Cusco")

    missing = client.post(
        QUERIES_URL,
        json={"text": QUESTION},
        headers=_auth(farmer_a["token"]),
    )
    assert missing.status_code == 409

    context_a = _create_and_select_context(farmer_a["token"], crop="papa", region="Huancayo")
    response = client.post(
        QUERIES_URL,
        json={"text": QUESTION},
        headers=_auth(farmer_a["token"]),
    )
    assert response.status_code == 201
    body = response.json()
    assert body["context"]["id"] == context_a["id"]
    assert body["context"]["id"] != context_b["id"]
    assert body["context"]["crop"] == "papa"


def test_submit_query_persists_query_and_response() -> None:
    user = _register_and_login()
    _create_and_select_context(user["token"])
    response = client.post(
        QUERIES_URL,
        json={"text": QUESTION},
        headers=_auth(user["token"]),
    )
    assert response.status_code == 201
    body = response.json()

    engine = create_mysql_engine(container.settings)
    with engine.connect() as connection:
        query_row = connection.execute(
            text("SELECT farmer_id, question_text FROM queries WHERE id = :id"),
            {"id": body["id"]},
        ).first()
        response_row = connection.execute(
            text(
                "SELECT answer_text, generation_method FROM responses WHERE query_id = :id"
            ),
            {"id": body["id"]},
        ).first()

    assert query_row is not None
    assert query_row[0] == user["farmer_id"]
    assert query_row[1] == QUESTION
    assert response_row is not None
    assert response_row[0] == body["answer"]
    assert response_row[1] == "template"
