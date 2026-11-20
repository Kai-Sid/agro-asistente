"""Helpers de cookie HttpOnly para JWT (OWASP A02/A07)."""

from __future__ import annotations

from fastapi import Response

from app.infrastructure.config.settings import Settings

COOKIE_NAME = "agro_access_token"


def establecer_cookie_auth(response: Response, token: str, settings: Settings) -> None:
    if not settings.auth_cookie_enabled:
        return
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,  # type: ignore[arg-type]
        max_age=max(60, int(settings.jwt_expire_minutes) * 60),
        path="/",
    )


def limpiar_cookie_auth(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        key=COOKIE_NAME,
        path="/",
        secure=settings.auth_cookie_secure,
        httponly=True,
        samesite=settings.auth_cookie_samesite,  # type: ignore[arg-type]
    )
