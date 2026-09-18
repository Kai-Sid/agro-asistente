from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field

from app.domain.exceptions import (
    DomainError,
    InvalidQueryTextError,
    InvalidTokenError,
    SelectedContextNotFoundError,
)
from app.domain.ports.input.submit_query_port import SubmitQueryCommand
from app.domain.valueObjects.query_text import QueryText
from app.infrastructure.composition import CompositionRoot


class SubmitQueryRequest(BaseModel):
    text: str = Field(min_length=1, max_length=QueryText.MAX_LENGTH)


class QueryContextResponse(BaseModel):
    id: str
    crop: str
    region: str
    plot_name: str | None


class QueryEvidenceResponse(BaseModel):
    document_id: str
    document_title: str
    chunk_id: str
    excerpt: str
    similarity_score: float
    rank_order: int


class SubmitQueryResponse(BaseModel):
    id: str
    text: str
    answer: str
    generation_method: str
    created_at: str
    context: QueryContextResponse
    evidences: list[QueryEvidenceResponse]


def create_query_router(container: CompositionRoot) -> APIRouter:
    router = APIRouter(prefix="/api/v1/queries", tags=["queries"])

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
        response_model=SubmitQueryResponse,
    )
    def submit_query(
        payload: SubmitQueryRequest,
        farmer_id: str = Depends(current_farmer_id),
    ) -> SubmitQueryResponse:
        command = SubmitQueryCommand(farmer_id=farmer_id, text=payload.text)
        try:
            result = container.submit_query_port.execute(command)
        except InvalidQueryTextError as error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error),
            ) from error
        except SelectedContextNotFoundError as error:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(error),
            ) from error
        except DomainError as error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error),
            ) from error
        return SubmitQueryResponse(
            id=result.id,
            text=result.text,
            answer=result.answer,
            generation_method=result.generation_method,
            created_at=result.created_at,
            context=QueryContextResponse(
                id=result.context.id,
                crop=result.context.crop,
                region=result.context.region,
                plot_name=result.context.plot_name,
            ),
            evidences=[
                QueryEvidenceResponse(
                    document_id=item.document_id,
                    document_title=item.document_title,
                    chunk_id=item.chunk_id,
                    excerpt=item.excerpt,
                    similarity_score=item.similarity_score,
                    rank_order=item.rank_order,
                )
                for item in result.evidences
            ],
        )

    return router
