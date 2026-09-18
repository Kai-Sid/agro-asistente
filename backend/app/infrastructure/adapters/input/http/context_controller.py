from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field

from app.domain.exceptions import (
    ContextNotFoundError,
    DomainError,
    InvalidContextDataError,
    InvalidTokenError,
)
from app.domain.ports.input.manage_context_port import (
    CreateAgriculturalContextCommand,
    SelectAgriculturalContextCommand,
)
from app.infrastructure.composition import CompositionRoot


class CreateContextRequest(BaseModel):
    plot_name: str | None = None
    crop: str = Field(min_length=1)
    region: str = Field(min_length=1)
    notes: str | None = None


class AgriculturalContextResponse(BaseModel):
    id: str
    farmer_id: str
    plot_name: str | None
    crop: str
    region: str
    notes: str | None
    is_selected: bool
    created_at: str


def create_context_router(container: CompositionRoot) -> APIRouter:
    router = APIRouter(prefix="/api/v1/contexts", tags=["contexts"])

    def current_farmer_id(
        authorization: str | None = Header(default=None),
    ) -> str:
        if not authorization or not authorization.lower().startswith("bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No autenticado",
            )
        token = authorization.split(" ", 1)[1].strip()
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No autenticado",
            )
        try:
            identity = container.token_verifier_port.verify(token)
        except InvalidTokenError as error:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(error),
            ) from error
        return identity.farmer_id

    @router.post(
        "",
        status_code=status.HTTP_201_CREATED,
        response_model=AgriculturalContextResponse,
    )
    def create_context(
        payload: CreateContextRequest,
        farmer_id: str = Depends(current_farmer_id),
    ) -> AgriculturalContextResponse:
        command = CreateAgriculturalContextCommand(
            farmer_id=farmer_id,
            plot_name=payload.plot_name,
            crop=payload.crop,
            region=payload.region,
            notes=payload.notes,
        )
        try:
            result = container.create_agricultural_context_port.execute(command)
        except InvalidContextDataError as error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error),
            ) from error
        except DomainError as error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error),
            ) from error
        return AgriculturalContextResponse(**result.__dict__)

    @router.get("", response_model=list[AgriculturalContextResponse])
    def list_contexts(
        farmer_id: str = Depends(current_farmer_id),
    ) -> list[AgriculturalContextResponse]:
        results = container.list_agricultural_contexts_port.execute(farmer_id)
        return [AgriculturalContextResponse(**item.__dict__) for item in results]

    @router.post(
        "/{context_id}/select",
        response_model=AgriculturalContextResponse,
    )
    def select_context(
        context_id: str,
        farmer_id: str = Depends(current_farmer_id),
    ) -> AgriculturalContextResponse:
        command = SelectAgriculturalContextCommand(
            farmer_id=farmer_id,
            context_id=context_id,
        )
        try:
            result = container.select_agricultural_context_port.execute(command)
        except ContextNotFoundError as error:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(error),
            ) from error
        except DomainError as error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error),
            ) from error
        return AgriculturalContextResponse(**result.__dict__)

    return router
