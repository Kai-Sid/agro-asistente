from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.infrastructure.config.settings import Settings


def registrar_cors(aplicacion: FastAPI, settings: Settings) -> None:
    """El comodín de métodos no abre el origen. El subdominio de Pages va por expresión regular."""
    aplicacion.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_origin_regex=settings.cors_origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
