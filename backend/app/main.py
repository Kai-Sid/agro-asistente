import os
import time
from uuid import uuid4

from fastapi import FastAPI

from app.infrastructure.config.cors import registrar_cors
from app.infrastructure.adapters.output.mysql.procedures import MysqlStoredProcedureGateway

from app.infrastructure.adapters.input.http.auth_controller import create_auth_router
from app.infrastructure.adapters.input.http.admin_controller import create_admin_router
from app.infrastructure.adapters.input.http.clasificacion_controller import (
    create_clasificacion_router,
)
from app.infrastructure.adapters.input.http.context_controller import create_context_router
from app.infrastructure.adapters.input.http.health_controller import create_health_router
from app.infrastructure.adapters.input.http.knowledge_controller import create_knowledge_router
from app.infrastructure.adapters.input.http.query_controller import create_query_router
from app.infrastructure.adapters.input.http.riesgo_controller import create_riesgo_router
from app.infrastructure.adapters.input.http.weather_controller import create_weather_router
from app.infrastructure.composition import build_container

container = build_container()

app = FastAPI(
    title=container.settings.app_name,
    version="0.1.0",
    description="PMV1 - Sistema de asistencia técnica agrícola basado en IA",
)


metric_gateway = MysqlStoredProcedureGateway(container.session_factory)


@app.middleware("http")
async def registrar_metrica_consulta(request, call_next):
    if request.method != "POST" or request.url.path != "/api/v1/queries":
        return await call_next(request)
    request_id = str(uuid4())
    inicio = time.perf_counter()
    codigo = 500
    try:
        response = await call_next(request)
        codigo = response.status_code
        return response
    finally:
        duracion_ms = max(0, int((time.perf_counter() - inicio) * 1000))
        try:
            metric_gateway.call(
                "sp_metrica_consulta_guardar",
                (request_id, codigo, duracion_ms),
            )
        except Exception:
            # La métrica no debe interrumpir una consulta agrícola.
            pass


registrar_cors(app, container.settings)

app.include_router(create_health_router(container))
app.include_router(create_auth_router(container))
app.include_router(create_admin_router(container))
app.include_router(create_context_router(container))
app.include_router(create_query_router(container))
app.include_router(create_knowledge_router(container))
app.include_router(create_weather_router(container))
app.include_router(create_clasificacion_router(container))
app.include_router(create_riesgo_router(container))


def host_de_escucha() -> str:
    """Producción escucha en todas las interfaces. El desarrollo local puede fijar otra."""
    return "0.0.0.0"


def puerto_de_escucha(environ: dict[str, str] | None = None) -> int:
    """Usa PORT y, si no existe, el 8000 del entorno local."""
    env = environ if environ is not None else os.environ
    bruto = str(env.get("PORT", "")).strip() or "8000"
    try:
        puerto = int(bruto)
    except ValueError as error:
        raise ValueError("PORT debe ser un entero entre 1 y 65535") from error
    if puerto < 1 or puerto > 65535:
        raise ValueError("PORT debe ser un entero entre 1 y 65535")
    return puerto


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=host_de_escucha(),
        port=puerto_de_escucha(),
        reload=False,
    )
