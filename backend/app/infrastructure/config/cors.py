from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.infrastructure.config.settings import Settings

METODOS_PERMITIDOS = ["GET", "POST", "OPTIONS"]
HEADERS_PERMITIDOS = ["Authorization", "Content-Type", "Accept"]


def registrar_cors(aplicacion: FastAPI, settings: Settings) -> None:
    """Orígenes acotados; métodos y headers explícitos (OWASP A05 / R-12)."""
    aplicacion.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_origin_regex=settings.cors_origin_regex,
        allow_credentials=True,
        allow_methods=METODOS_PERMITIDOS,
        allow_headers=HEADERS_PERMITIDOS,
    )
