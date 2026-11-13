"""Registro estructurado de eventos de seguridad (OWASP A09)."""

from __future__ import annotations

import logging
from typing import Any

_logger = logging.getLogger("agro.security")


def configurar_logging_seguridad() -> None:
    if _logger.handlers:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s [agro.security] %(message)s")
    )
    _logger.addHandler(handler)
    _logger.setLevel(logging.INFO)
    _logger.propagate = False


def log_seguridad(evento: str, habilitado: bool = True, **campos: Any) -> None:
    if not habilitado:
        return
    partes = [f"event={evento}"]
    for clave, valor in campos.items():
        if valor is None:
            continue
        texto = str(valor).replace("\n", " ").replace("\r", " ")
        if clave in {"password", "token", "authorization", "jwt"}:
            continue
        if clave == "email" and "@" in texto:
            local, _, dominio = texto.partition("@")
            texto = f"{local[:2]}***@{dominio}" if dominio else "***"
        partes.append(f"{clave}={texto}")
    _logger.info(" ".join(partes))
