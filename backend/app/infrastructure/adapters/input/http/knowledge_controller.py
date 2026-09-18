from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field

from app.domain.entities.knowledge_document import KnowledgeDocument
from app.domain.exceptions import (
    DomainError,
    DuplicateKnowledgeDocumentError,
    InvalidKnowledgeDocumentError,
    InvalidTokenError,
    KnowledgeFileNotFoundError,
)
from app.domain.ports.input.ingest_knowledge_port import IngestKnowledgeCommand
from app.infrastructure.composition import CompositionRoot


class IngestKnowledgeRequest(BaseModel):
    title: str = Field(min_length=1, max_length=KnowledgeDocument.TITLE_MAX_LENGTH)
    topic: str = Field(min_length=1, max_length=KnowledgeDocument.TOPIC_MAX_LENGTH)
    content: str = Field(min_length=1, max_length=KnowledgeDocument.CONTENT_MAX_LENGTH)


class KnowledgeDocumentResponse(BaseModel):
    id: str
    title: str
    topic: str
    source_path: str
    content_hash: str
    chunk_count: int
    ingested_at: str
    status: str


class IndexKnowledgeResponse(BaseModel):
    indexed_documents: int
    total_chunks: int
    collection: str
    documents: list[KnowledgeDocumentResponse]


def create_knowledge_router(container: CompositionRoot) -> APIRouter:
    router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])

    def require_authenticated_farmer(
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
        "/ingest",
        status_code=status.HTTP_201_CREATED,
        response_model=KnowledgeDocumentResponse,
    )
    def ingest_knowledge(
        payload: IngestKnowledgeRequest,
        _farmer_id: str = Depends(require_authenticated_farmer),
    ) -> KnowledgeDocumentResponse:
        command = IngestKnowledgeCommand(
            title=payload.title,
            topic=payload.topic,
            content=payload.content,
        )
        try:
            result = container.ingest_knowledge_port.execute(command)
        except DuplicateKnowledgeDocumentError as error:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(error),
            ) from error
        except InvalidKnowledgeDocumentError as error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error),
            ) from error
        except DomainError as error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error),
            ) from error
        return KnowledgeDocumentResponse(**result.__dict__)

    @router.post("/index", response_model=IndexKnowledgeResponse)
    def index_knowledge(
        _farmer_id: str = Depends(require_authenticated_farmer),
    ) -> IndexKnowledgeResponse:
        try:
            result = container.index_knowledge_port.execute()
        except KnowledgeFileNotFoundError as error:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(error),
            ) from error
        except DomainError as error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error),
            ) from error
        return IndexKnowledgeResponse(
            indexed_documents=result.indexed_documents,
            total_chunks=result.total_chunks,
            collection=container.settings.chroma_collection,
            documents=[KnowledgeDocumentResponse(**item.__dict__) for item in result.documents],
        )

    @router.get("/documents", response_model=list[KnowledgeDocumentResponse])
    def list_knowledge_documents(
        _farmer_id: str = Depends(require_authenticated_farmer),
    ) -> list[KnowledgeDocumentResponse]:
        results = container.list_knowledge_documents_port.execute()
        return [KnowledgeDocumentResponse(**item.__dict__) for item in results]

    return router
