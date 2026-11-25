from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr, Field

from app.infrastructure.adapters.input.http.dependencia_autenticacion import (
    dependencia_administrador_autenticado,
)
from app.infrastructure.adapters.output.mysql.procedures import MysqlStoredProcedureGateway
from app.infrastructure.composition import CompositionRoot


class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str = "ADMINISTRADOR"
    name: str
    email: str


def create_admin_router(container: CompositionRoot) -> APIRouter:
    router = APIRouter(prefix="/api/v1/admin", tags=["administration"])
    procedures = MysqlStoredProcedureGateway(container.session_factory)
    current_admin = dependencia_administrador_autenticado(container)

    @router.post("/auth/login", response_model=AdminLoginResponse)
    def login(payload: AdminLoginRequest) -> AdminLoginResponse:
        email = str(payload.email).strip().lower()
        rows = procedures.call("sp_administrador_buscar_por_correo", (email,))
        if not rows or not container.puerto_hasher_contrasena.verificar_contrasena(
            payload.password, str(rows[0]["contrasena_hash"])
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas",
                headers={"WWW-Authenticate": "Bearer"},
            )
        admin = rows[0]
        token = container.puerto_emisor_token.emitir_token(
            sujeto=str(admin["id"]),
            claims={"email": email, "rol": "ADMINISTRADOR"},
        )
        return AdminLoginResponse(
            access_token=token,
            name=str(admin["nombre"]),
            email=email,
        )

    @router.get("/metrics")
    def metrics(
        days: int = Query(default=30, ge=1, le=365),
        _admin_id: str = Depends(current_admin),
    ) -> dict[str, object]:
        rows = procedures.call("sp_metricas_consulta_resumen", (days,))
        summary = rows[0] if rows else {}
        return {
            "days": days,
            "total_requests": int(summary.get("total_solicitudes") or 0),
            "queries_attended": int(summary.get("consultas_atendidas") or 0),
            "requests_with_error": int(summary.get("solicitudes_con_error") or 0),
            "average_response_ms": float(summary.get("promedio_ms") or 0),
            "maximum_response_ms": int(summary.get("maximo_ms") or 0),
        }

    return router
