from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.infrastructure.adapters.input.http.auth_controller import create_auth_router
from app.infrastructure.adapters.input.http.context_controller import create_context_router
from app.infrastructure.adapters.input.http.health_controller import create_health_router
from app.infrastructure.adapters.input.http.knowledge_controller import create_knowledge_router
from app.infrastructure.adapters.input.http.query_controller import create_query_router
from app.infrastructure.adapters.input.http.weather_controller import create_weather_router
from app.infrastructure.composition import build_container

container = build_container()

app = FastAPI(
    title=container.settings.app_name,
    version="0.1.0",
    description="PMV1 - Sistema de asistencia técnica agrícola basado en IA",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=container.settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(create_health_router(container))
app.include_router(create_auth_router(container))
app.include_router(create_context_router(container))
app.include_router(create_query_router(container))
app.include_router(create_knowledge_router(container))
app.include_router(create_weather_router(container))
