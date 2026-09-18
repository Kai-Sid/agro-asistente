from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.domain.exceptions import (
    DomainError,
    DuplicateEmailError,
    InvalidCredentialsError,
    InvalidEmailError,
    InvalidFarmerDataError,
    InvalidPasswordError,
)
from app.domain.ports.input.login_farmer_port import LoginFarmerCommand
from app.domain.ports.input.register_farmer_port import RegisterFarmerCommand
from app.infrastructure.composition import CompositionRoot


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


class LoginFarmerResponse(BaseModel):
    access_token: str
    token_type: str
    farmer: AuthenticatedFarmerResponse


def create_auth_router(container: CompositionRoot) -> APIRouter:
    router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

    @router.post(
        "/register",
        status_code=status.HTTP_201_CREATED,
        response_model=RegisterFarmerResponse,
    )
    def register(payload: RegisterFarmerRequest) -> RegisterFarmerResponse:
        command = RegisterFarmerCommand(
            names=payload.names,
            last_names=payload.last_names,
            email=payload.email,
            password=payload.password,
        )
        try:
            result = container.register_farmer_port.execute(command)
        except DuplicateEmailError as error:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(error),
            ) from error
        except (InvalidEmailError, InvalidPasswordError, InvalidFarmerDataError) as error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error),
            ) from error
        except DomainError as error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error),
            ) from error

        return RegisterFarmerResponse(
            id=result.id,
            names=result.names,
            last_names=result.last_names,
            email=result.email,
        )

    @router.post(
        "/login",
        status_code=status.HTTP_200_OK,
        response_model=LoginFarmerResponse,
    )
    def login(payload: LoginFarmerRequest) -> LoginFarmerResponse:
        command = LoginFarmerCommand(email=payload.email, password=payload.password)
        try:
            result = container.login_farmer_port.execute(command)
        except InvalidCredentialsError as error:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(error),
            ) from error
        except InvalidEmailError as error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error),
            ) from error
        except DomainError as error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error),
            ) from error

        return LoginFarmerResponse(
            access_token=result.access_token,
            token_type=result.token_type,
            farmer=AuthenticatedFarmerResponse(
                id=result.farmer.id,
                names=result.farmer.names,
                last_names=result.farmer.last_names,
                email=result.farmer.email,
            ),
        )

    return router
