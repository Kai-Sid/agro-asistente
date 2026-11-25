from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.domain.exceptions import ErrorTokenInvalido
from app.domain.ports.output.token_verifier_port import IdentidadAutenticada
from app.infrastructure.composition import CompositionRoot

esquema_bearer_jwt = HTTPBearer(
    auto_error=False,
    scheme_name="BearerJWT",
    bearerFormat="JWT",
    description="JWT obtenido en POST /api/v1/auth/login.",
)


def _identidad_desde_credenciales(
    container: CompositionRoot,
    credenciales: HTTPAuthorizationCredentials | None,
) -> IdentidadAutenticada:
    token = credenciales.credentials.strip() if credenciales is not None else ""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return container.puerto_verificador_token.verificar(token)
    except ErrorTokenInvalido as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error


def dependencia_agricultor_autenticado(container: CompositionRoot) -> Callable[..., str]:
    """Valida el token y exige que la identidad tenga rol de agricultor."""

    def agricultor_autenticado(
        credenciales: HTTPAuthorizationCredentials | None = Depends(esquema_bearer_jwt),
    ) -> str:
        identidad = _identidad_desde_credenciales(container, credenciales)
        if identidad.rol != "AGRICULTOR":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para realizar esta acción",
            )
        return identidad.agricultor_id

    return agricultor_autenticado


def dependencia_administrador_autenticado(container: CompositionRoot) -> Callable[..., str]:
    """Valida el token y exige rol de administrador."""

    def administrador_autenticado(
        credenciales: HTTPAuthorizationCredentials | None = Depends(esquema_bearer_jwt),
    ) -> str:
        identidad = _identidad_desde_credenciales(container, credenciales)
        if identidad.rol != "ADMINISTRADOR":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para realizar esta acción",
            )
        return identidad.agricultor_id

    return administrador_autenticado
