#!/usr/bin/env python3
"""Smoke E2E: health → registro/login → contexto → consulta con Ollama.

No inventa métricas. Si Ollama o MySQL no están, sale con código distinto de 0.

Uso (desde backend/, venv activo):
  set RUN_OLLAMA_INTEGRATION_TESTS=true
  python scripts/smoke_e2e_ollama.py

Variables opcionales:
  SMOKE_API_BASE=http://127.0.0.1:8000
  SMOKE_OLLAMA_BASE=http://127.0.0.1:11434
"""

from __future__ import annotations

import os
import sys
import time
import uuid
from typing import Any

import httpx

API_BASE = os.environ.get("SMOKE_API_BASE", "http://127.0.0.1:8000").rstrip("/")
OLLAMA_BASE = os.environ.get("SMOKE_OLLAMA_BASE", "http://127.0.0.1:11434").rstrip("/")
TIMEOUT = float(os.environ.get("SMOKE_TIMEOUT_SECONDS", "120"))


def _fail(msg: str, code: int = 1) -> None:
    print(f"[FAIL] {msg}", file=sys.stderr)
    raise SystemExit(code)


def _ok(msg: str) -> None:
    print(f"[OK] {msg}")


def check_ollama(client: httpx.Client) -> None:
    try:
        r = client.get(f"{OLLAMA_BASE}/api/tags", timeout=10.0)
    except httpx.HTTPError as error:
        _fail(f"Ollama no responde en {OLLAMA_BASE}: {error}")
    if r.status_code != 200:
        _fail(f"Ollama /api/tags → HTTP {r.status_code}")
    models = [m.get("name", "") for m in (r.json().get("models") or [])]
    _ok(f"Ollama disponible ({len(models)} modelo(s))")


def check_health(client: httpx.Client) -> None:
    r = client.get(f"{API_BASE}/health", timeout=30.0)
    if r.status_code != 200:
        _fail(f"/health → HTTP {r.status_code}: {r.text}")
    _ok(f"/health → {r.json()}")


def register_login(client: httpx.Client) -> str:
    email = f"smoke-{uuid.uuid4().hex[:10]}@example.com"
    password = "Password123!"
    reg = client.post(
        f"{API_BASE}/api/v1/auth/register",
        json={
            "names": "Smoke",
            "last_names": "Ollama",
            "email": email,
            "password": password,
        },
        timeout=30.0,
    )
    if reg.status_code != 201:
        _fail(f"register → HTTP {reg.status_code}: {reg.text}")
    login = client.post(
        f"{API_BASE}/api/v1/auth/login",
        json={"email": email, "password": password},
        timeout=30.0,
    )
    if login.status_code != 200:
        _fail(f"login → HTTP {login.status_code}: {login.text}")
    token = login.json().get("access_token")
    if not token:
        _fail("login sin access_token")
    _ok(f"auth ok ({email})")
    return str(token)


def ensure_context(client: httpx.Client, headers: dict[str, str]) -> None:
    created = client.post(
        f"{API_BASE}/api/v1/contexts",
        headers=headers,
        json={"crop": "papa", "region": "Huancayo", "plot_name": "Smoke E2E"},
        timeout=30.0,
    )
    if created.status_code != 201:
        _fail(f"create context → HTTP {created.status_code}: {created.text}")
    ctx_id = created.json()["id"]
    selected = client.post(
        f"{API_BASE}/api/v1/contexts/{ctx_id}/select",
        headers=headers,
        timeout=30.0,
    )
    if selected.status_code not in {200, 201, 204}:
        _fail(f"select context → HTTP {selected.status_code}: {selected.text}")
    _ok(f"contexto seleccionado {ctx_id}")


def submit_query(client: httpx.Client, headers: dict[str, str]) -> dict[str, Any]:
    started = time.monotonic()
    r = client.post(
        f"{API_BASE}/api/v1/queries",
        headers=headers,
        json={"text": "¿Cómo riego la papa en floración en sierra?"},
        timeout=TIMEOUT,
    )
    elapsed = time.monotonic() - started
    if r.status_code != 201:
        _fail(f"query → HTTP {r.status_code}: {r.text}")
    body = r.json()
    method = body.get("generation_method")
    answer = (body.get("answer") or "").strip()
    if method != "ollama":
        _fail(
            f"generation_method={method!r} (esperado 'ollama'). "
            "Revise GENERATION_PROVIDER y que el API no use plantilla."
        )
    if not answer:
        _fail("respuesta vacía de Ollama")
    _ok(f"consulta ollama en {elapsed:.1f}s ({len(answer)} chars)")
    return body


def main() -> None:
    flag = (
        os.environ.get("RUN_OLLAMA_INTEGRATION_TESTS")
        or os.environ.get("OLLAMA_INTEGRATION")
        or ""
    ).strip().lower()
    if flag not in {"1", "true", "yes"}:
        _fail(
            "Active RUN_OLLAMA_INTEGRATION_TESTS=true antes del smoke "
            "(evita ejecuciones accidentales sin Ollama).",
            code=2,
        )

    with httpx.Client() as client:
        check_ollama(client)
        check_health(client)
        token = register_login(client)
        headers = {"Authorization": f"Bearer {token}"}
        ensure_context(client, headers)
        submit_query(client, headers)
    print("[PASS] smoke E2E Ollama completado")


if __name__ == "__main__":
    main()
