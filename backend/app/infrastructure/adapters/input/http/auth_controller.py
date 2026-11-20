from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel, Field

from app.domain.exceptions import (
    ErrorContrasenaInvalida,
    ErrorCorreoDuplicado,
    ErrorCorreoInvalido,
    ErrorCredencialesInvalidas,
    ErrorDatosAgricultorInvalidos,
    ErrorDominio,
)
from app.domain.ports.input.iniciar_sesion_agricultor_port import ComandoIniciarSesionAgricultor
from app.domain.ports.input.registrar_agricultor_port import ComandoRegistrarAgricultor
from app.infrastructure.auth_cookie import establecer_cookie_auth, limpiar_cookie_auth
from app.infrastructure.composition import CompositionRoot
from app.infrastructure.rate_limit import limitador_global
from app.infrastructure.security_logging import log_seguridad


class RegisterFarmerRequest(BaseModel):
    names: str = Field(min_length=1)
    last_names: str = Field(min_length=1)
    email: str = Field(min_length=1)
    password: str = Field(min_length=1)


class RegisterFarmerResponse(BaseModel):
    id: str
    names: str
    last_names: str
    email: str


class LoginFarmerRequest(BaseModel):
    email: str = Field(min_length=1)
    password: str = Field(min_length=1)


class AuthenticatedFarmerResponse(BaseModel):
    id: str
    names: str
    last_names: str
    email: str
    role: str = "farmer"


class LoginFarmerResponse(BaseModel):
    access_token: str
    token_type: str
    farmer: AuthenticatedFarmerResponse


def _cliente_ip(request: Request) -> str:
    reenviada = request.headers.get("x-forwarded-for", "")
    if reenviada:
        return reenviada.split(",")[0].strip() or "unknown"
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def _aplicar_rate_limit(
    container: CompositionRoot,
    *,
    accion: str,
    clave: str,
    maximo: int,
    ventana: int,
) -> None:
    if not container.settings.rate_limit_enabled:
        return
    if limitador_global.permitir(f"{accion}:{clave}", maximo, ventana):
        return
    log_seguridad(
        "rate_limited",
        habilitado=container.settings.security_log_enabled,
        action=accion,
        key=clave,
    )
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="Demasiadas solicitudes. Inténtalo más tarde.",
        headers={"Retry-After": str(ventana)},
    )


def create_auth_router(container: CompositionRoot) -> APIRouter:
    router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

    @router.post(
        "/register",
        status_code=status.HTTP_201_CREATED,
        response_model=RegisterFarmerResponse,
    )
    def register(payload: RegisterFarmerRequest, request: Request) -> RegisterFarmerResponse:
        ip = _cliente_ip(request)
        _aplicar_rate_limit(
            container,
            accion="register",
            clave=ip,
            maximo=container.settings.rate_limit_register_max,
            ventana=container.settings.rate_limit_register_window_seconds,
        )
        command = ComandoRegistrarAgricultor(
            nombres=payload.names,
            apellidos=payload.last_names,
            email=payload.email,
            contrasena=payload.password,
        )
        try:
            result = container.puerto_registrar_agricultor.ejecutar(command)
        except ErrorCorreoDuplicado as error:
            log_seguridad(
                "register_conflict",
                habilitado=container.settings.security_log_enabled,
                email=payload.email,
                ip=ip,
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(error),
            ) from error
        except (ErrorCorreoInvalido, ErrorContrasenaInvalida, ErrorDatosAgricultorInvalidos) as error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error),
            ) from error
        except ErrorDominio as error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error),
            ) from error

        log_seguridad(
            "register_ok",
            habilitado=container.settings.security_log_enabled,
            farmer_id=result.id,
            email=result.email,
            ip=ip,
        )
        return RegisterFarmerResponse(
            id=result.id,
            names=result.nombres,
            last_names=result.apellidos,
            email=result.email,
        )

    @router.post(
        "/login",
        status_code=status.HTTP_200_OK,
        response_model=LoginFarmerResponse,
    )
    def login(
        payload: LoginFarmerRequest,
        request: Request,
        response: Response,
    ) -> LoginFarmerResponse:
        ip = _cliente_ip(request)
        email_clave = (payload.email or "").strip().lower() or "unknown"
        _aplicar_rate_limit(
            container,
            accion="login",
            clave=f"{ip}:{email_clave}",
            maximo=container.settings.rate_limit_login_max,
            ventana=container.settings.rate_limit_login_window_seconds,
        )
        command = ComandoIniciarSesionAgricultor(
            email=payload.email,
            contrasena=payload.password,
        )
        try:
            result = container.puerto_iniciar_sesion_agricultor.ejecutar(command)
        except ErrorCredencialesInvalidas as error:
            log_seguridad(
                "login_fail",
                habilitado=container.settings.security_log_enabled,
                email=payload.email,
                ip=ip,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(error),
            ) from error
        except ErrorCorreoInvalido as error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error),
            ) from error
        except ErrorDominio as error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error),
            ) from error

        log_seguridad(
            "login_ok",
            habilitado=container.settings.security_log_enabled,
            farmer_id=result.agricultor.id,
            email=result.agricultor.email,
            role=result.agricultor.rol,
            ip=ip,
        )
        establecer_cookie_auth(response, result.access_token, container.settings)
        return LoginFarmerResponse(
            access_token=result.access_token,
            token_type=result.token_type,
            farmer=AuthenticatedFarmerResponse(
                id=result.agricultor.id,
                names=result.agricultor.nombres,
                last_names=result.agricultor.apellidos,
                email=result.agricultor.email,
                role=result.agricultor.rol,
            ),
        )

    @router.post("/logout", status_code=status.HTTP_200_OK)
    def logout(response: Response) -> dict[str, str]:
        limpiar_cookie_auth(response, container.settings)
        log_seguridad(
            "logout",
            habilitado=container.settings.security_log_enabled,
        )
        return {"status": "ok"}

    return router
