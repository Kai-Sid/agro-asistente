"""Estado de trabajos en cola (indexación / consultas largas)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.domain.ports.output.token_verifier_port import IdentidadAutenticada
from app.infrastructure.adapters.input.http.dependencia_autenticacion import (
    dependencia_identidad_autenticada,
)
from app.infrastructure.composition import CompositionRoot
from app.infrastructure.job_queue import cola_trabajos


class JobStatusResponse(BaseModel):
    id: str
    job_type: str
    status: str
    result: dict | None = None
    error: str | None = None
    created_at: str
    updated_at: str


def create_jobs_router(container: CompositionRoot) -> APIRouter:
    router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])
    identidad = dependencia_identidad_autenticada(container)

    @router.get("/{job_id}", response_model=JobStatusResponse)
    def obtener_trabajo(
        job_id: str,
        actor: IdentidadAutenticada = Depends(identidad),
    ) -> JobStatusResponse:
        if not container.settings.async_jobs_enabled:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Cola asíncrona deshabilitada (ASYNC_JOBS_ENABLED=false).",
            )
        job = cola_trabajos.get(job_id)
        if job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Trabajo no encontrado.",
            )
        if job.farmer_id and job.farmer_id != actor.agricultor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No autorizado a consultar este trabajo.",
            )
        return JobStatusResponse(
            id=job.id,
            job_type=job.job_type,
            status=job.status.value,
            result=job.result,
            error=job.error,
            created_at=job.created_at,
            updated_at=job.updated_at,
        )

    return router
