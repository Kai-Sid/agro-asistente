"""Verificación SHA-256 de artefactos .joblib antes de cargarlos."""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

_logger = logging.getLogger("agro.security")

# Hashes de los modelos versionados en el repositorio (commit de remediación OWASP).
HASHES_ESPERADOS: dict[str, str] = {
    "modelo_tfidf_logreg_v2.joblib": (
        "5638fad7c889f62cceed91a13ea8174e45e5fd9119b226dbb9486751fbd1cfd2"
    ),
    "modelo_riesgo_hu08.joblib": (
        "2f3997c1101433c24f4ebdf7f62ecefaa83d782cb34b86a3484705e8bde133bb"
    ),
}


def sha256_archivo(ruta: Path) -> str:
    digest = hashlib.sha256()
    with ruta.open("rb") as handle:
        for bloque in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(bloque)
    return digest.hexdigest()


def verificar_integridad_modelo(
    ruta: Path,
    *,
    enforce: bool,
    hashes: dict[str, str] | None = None,
) -> None:
    """Si enforce=True y el hash no coincide, lanza ValueError.
    Si enforce=False, solo registra warning.
    """
    esperados = hashes if hashes is not None else HASHES_ESPERADOS
    nombre = ruta.name
    esperado = esperados.get(nombre)
    if esperado is None:
        mensaje = f"Sin hash registrado para {nombre}; se omite verificación."
        if enforce:
            raise ValueError(mensaje)
        _logger.warning(mensaje)
        return
    if not ruta.is_file():
        return
    actual = sha256_archivo(ruta)
    if actual.lower() != esperado.lower():
        mensaje = (
            f"Integridad de modelo fallida para {nombre}: "
            f"esperado {esperado[:16]}… obtenido {actual[:16]}…"
        )
        if enforce:
            raise ValueError(mensaje)
        _logger.warning("%s (MODEL_INTEGRITY_CHECK en modo aviso)", mensaje)


def escribir_manifiesto_hashes(ruta_salida: Path, rutas: list[Path]) -> None:
    payload = {path.name: sha256_archivo(path) for path in rutas if path.is_file()}
    ruta_salida.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
