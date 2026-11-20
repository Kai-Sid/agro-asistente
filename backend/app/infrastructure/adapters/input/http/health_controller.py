from fastapi import APIRouter, HTTPException, status

from app.infrastructure.adapters.output.mysql.connection import ping_mysql
from app.infrastructure.composition import CompositionRoot


def create_health_router(container: CompositionRoot) -> APIRouter:
    router = APIRouter(tags=["health"])

    @router.get("/health")
    def health() -> dict[str, str]:
        if not container.settings.health_incluye_detalle:
            return {"status": "ok"}
        mysql_status = "connected" if ping_mysql(container.settings) else "disconnected"
        return {
            "status": "ok",
            "service": container.settings.app_name,
            "phase": "1",
            "architecture": "hexagonal",
            "mysql": mysql_status,
        }

    @router.get("/health/ready")
    def ready() -> dict[str, str]:
        """Readiness: falla si MySQL no responde (útil para orquestadores / ops)."""
        mysql_ok = ping_mysql(container.settings)
        if not mysql_ok:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "status": "not_ready",
                    "mysql": "disconnected",
                },
            )
        return {
            "status": "ready",
            "mysql": "connected",
            "service": container.settings.app_name,
        }

    return router
