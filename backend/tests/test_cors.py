from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.infrastructure.config.cors import registrar_cors
from app.infrastructure.config.settings import Settings

ORIGEN_PRINCIPAL = "https://agro-asistente.pages.dev"
ORIGEN_DESPLIEGUE = "https://58956d7.agro-asistente.pages.dev"
ORIGEN_AJENO = "https://otro.example"


def aplicacion(cors_origins: str) -> TestClient:
    settings = Settings(_env_file=None, cors_origins=cors_origins)
    app = FastAPI()
    registrar_cors(app, settings)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return TestClient(app)


def test_cors_se_registra_antes_de_las_rutas() -> None:
    texto = (Path(__file__).resolve().parents[1] / "app" / "main.py").read_text(encoding="utf-8")
    assert texto.index("registrar_cors(") < texto.index("include_router(")
    assert 'allow_origins=["*"]' not in texto
    assert "allow_origins=settings.cors_origin_list" in (
        Path(__file__).resolve().parents[1] / "app" / "infrastructure" / "config" / "cors.py"
    ).read_text(encoding="utf-8")


def test_options_y_get_admiten_el_dominio_principal_y_el_despliegue() -> None:
    client = aplicacion(
        "http://localhost:5173,https://agro-asistente.pages.dev,https://*.agro-asistente.pages.dev"
    )
    for origen in (ORIGEN_PRINCIPAL, ORIGEN_DESPLIEGUE, "http://localhost:5173"):
        options = client.options(
            "/health",
            headers={
                "Origin": origen,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization",
            },
        )
        assert options.status_code == 200
        assert options.headers["access-control-allow-origin"] == origen
        assert options.headers["access-control-allow-credentials"] == "true"
        assert options.headers["access-control-allow-origin"] != "*"
        assert "GET" in options.headers["access-control-allow-methods"]
        assert "authorization" in options.headers["access-control-allow-headers"].lower()

        respuesta = client.get("/health", headers={"Origin": origen})
        assert respuesta.status_code == 200
        assert respuesta.json()["status"] == "ok"
        assert respuesta.headers["access-control-allow-origin"] == origen


def test_el_subdominio_responde_aunque_solo_este_configurado_el_dominio_principal() -> None:
    client = aplicacion("https://agro-asistente.pages.dev")
    options = client.options(
        "/health",
        headers={
            "Origin": ORIGEN_DESPLIEGUE,
            "Access-Control-Request-Method": "GET",
        },
    )
    consulta = client.get("/health", headers={"Origin": ORIGEN_DESPLIEGUE})

    assert options.status_code == 200
    assert options.headers["access-control-allow-origin"] == ORIGEN_DESPLIEGUE
    assert consulta.status_code == 200
    assert consulta.headers["access-control-allow-origin"] == ORIGEN_DESPLIEGUE


def test_un_origen_ajeno_no_recibe_permiso() -> None:
    client = aplicacion("https://agro-asistente.pages.dev")
    for origen in (
        ORIGEN_AJENO,
        "http://58956d7.agro-asistente.pages.dev",
        "https://a.b.agro-asistente.pages.dev",
        "https://agro-asistente.pages.dev.evil.com",
    ):
        options = client.options(
            "/health",
            headers={
                "Origin": origen,
                "Access-Control-Request-Method": "GET",
            },
        )
        consulta = client.get("/health", headers={"Origin": origen})

        assert options.status_code == 400
        assert "access-control-allow-origin" not in consulta.headers
        assert consulta.status_code == 200
