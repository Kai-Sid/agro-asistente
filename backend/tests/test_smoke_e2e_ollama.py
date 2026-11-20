"""Smoke E2E automatizado con Ollama (integration; skip por defecto).

Flujo: register → login → contexto → consulta RAG/Ollama.
Complementa `scripts/smoke_e2e_ollama.py` (contra API en proceso separado).
"""

from __future__ import annotations

import os
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient

from app.infrastructure.adapters.output.generation.adaptador_generacion_ollama import (
    AdaptadorGeneracionOllama,
)
from app.infrastructure.config.settings import Settings
from app.main import app, container

client = TestClient(app)


def _integracion_habilitada() -> bool:
    valor = (
        os.environ.get("RUN_OLLAMA_INTEGRATION_TESTS")
        or os.environ.get("OLLAMA_INTEGRATION")
        or ""
    ).strip().lower()
    return valor in {"1", "true", "yes"}


def _ollama_disponible(settings: Settings) -> bool:
    try:
        r = httpx.get(f"{settings.ollama_base_url.rstrip('/')}/api/tags", timeout=5.0)
        return r.status_code == 200
    except httpx.HTTPError:
        return False


@pytest.mark.integration
@pytest.mark.skipif(
    not _integracion_habilitada(),
    reason="Active RUN_OLLAMA_INTEGRATION_TESTS=true; requiere Ollama real.",
)
def test_smoke_e2e_consulta_con_ollama() -> None:
    settings = Settings(_env_file=None)
    if not _ollama_disponible(settings):
        pytest.skip(f"Ollama no disponible en {settings.ollama_base_url}")

    adaptador = AdaptadorGeneracionOllama(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
        timeout_seconds=settings.ollama_timeout_seconds,
    )
    caso = container.puerto_registrar_consulta
    previo = caso._generacion_texto
    caso._generacion_texto = adaptador
    try:
        email = f"e2e-{uuid4().hex[:8]}@example.com"
        password = "Password123!"
        reg = client.post(
            "/api/v1/auth/register",
            json={
                "names": "E2E",
                "last_names": "Ollama",
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
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

        created = client.post(
            "/api/v1/contexts",
            headers=headers,
            json={"crop": "papa", "region": "Huancayo", "plot_name": "E2E"},
        )
        assert created.status_code == 201, created.text
        ctx_id = created.json()["id"]
        selected = client.post(
            f"/api/v1/contexts/{ctx_id}/select",
            headers=headers,
        )
        assert selected.status_code in {200, 201, 204}, selected.text

        query = client.post(
            "/api/v1/queries",
            headers=headers,
            json={"text": "¿Cómo riego la papa en floración?"},
        )
        assert query.status_code == 201, query.text
        body = query.json()
        assert body.get("generation_method") == "ollama"
        assert (body.get("answer") or "").strip()
    finally:
        caso._generacion_texto = previo
