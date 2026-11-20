from collections.abc import Callable

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.domain.exceptions import ErrorTokenInvalido
from app.domain.ports.output.token_verifier_port import IdentidadAutenticada
from app.infrastructure.auth_cookie import COOKIE_NAME
from app.infrastructure.composition import CompositionRoot
from app.infrastructure.security_logging import log_seguridad

esquema_bearer_jwt = HTTPBearer(
    auto_error=False,
    scheme_name="BearerJWT",
    bearerFormat="JWT",
    description="JWT obtenido en POST /api/v1/auth/login.",
)


def _token_desde_request(
    request: Request,
    credenciales: HTTPAuthorizationCredentials | None,
    *,
    cookie_habilitada: bool,
) -> str:
    if credenciales is not None and credenciales.credentials.strip():
        return credenciales.credentials.strip()
    if cookie_habilitada:
        cookie = (request.cookies.get(COOKIE_NAME) or "").strip()
        if cookie:
            return cookie
    return ""


def dependencia_identidad_autenticada(
    container: CompositionRoot,
) -> Callable[..., IdentidadAutenticada]:
    """Valida Bearer token o cookie HttpOnly y devuelve la identidad completa."""

    def identidad_autenticada(
        request: Request,
        credenciales: HTTPAuthorizationCredentials | None = Depends(esquema_bearer_jwt),
    ) -> IdentidadAutenticada:
        token = _token_desde_request(
            request,
            credenciales,
            cookie_habilitada=container.settings.auth_cookie_enabled,
        )
        if not token:
            log_seguridad(
                "auth_denied",
                habilitado=container.settings.security_log_enabled,
                reason="missing_token",
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No autenticado",
                headers={"WWW-Authenticate": "Bearer"},
            )
        try:
            identidad = container.puerto_verificador_token.verificar(token)
        except ErrorTokenInvalido as error:
            log_seguridad(
                "auth_denied",
                habilitado=container.settings.security_log_enabled,
                reason="invalid_token",
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(error),
                headers={"WWW-Authenticate": "Bearer"},
            ) from error
        return identidad

    return identidad_autenticada


def dependencia_agricultor_autenticado(container: CompositionRoot) -> Callable[..., str]:
    """Extrae el id del agricultor autenticado (compatibilidad con controladores existentes)."""

    identidad_dep = dependencia_identidad_autenticada(container)

    def agricultor_autenticado(
        identidad: IdentidadAutenticada = Depends(identidad_dep),
    ) -> str:
        return identidad.agricultor_id

    return agricultor_autenticado


def dependencia_escritura_conocimiento(
    container: CompositionRoot,
) -> Callable[..., str]:
    """Permite mutaciones de knowledge según KNOWLEDGE_MUTATION_POLICY."""

    identidad_dep = dependencia_identidad_autenticada(container)

    def escritor_conocimiento(
        identidad: IdentidadAutenticada = Depends(identidad_dep),
    ) -> str:
        politica = container.settings.knowledge_mutation_policy
        if politica == "curators_only" and identidad.rol != "curator":
            log_seguridad(
                "knowledge_forbidden",
                habilitado=container.settings.security_log_enabled,
                farmer_id=identidad.agricultor_id,
                role=identidad.rol,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Se requiere rol curator para modificar la base de conocimiento",
            )
        return identidad.agricultor_id

    return escritor_conocimiento
