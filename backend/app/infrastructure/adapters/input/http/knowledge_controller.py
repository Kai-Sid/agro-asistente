from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.domain.entities.documento_conocimiento import DocumentoConocimiento
from app.domain.exceptions import (
    ErrorArchivoConocimientoNoEncontrado,
    ErrorDocumentoConocimientoDuplicado,
    ErrorDocumentoConocimientoInvalido,
    ErrorDominio,
)
from app.domain.ports.input.incorporar_conocimiento_port import (
    ComandoIncorporarConocimiento,
    ResultadoDocumentoConocimiento,
)
from app.infrastructure.adapters.input.http.dependencia_autenticacion import (
    dependencia_agricultor_autenticado,
    dependencia_escritura_conocimiento,
)
from app.infrastructure.composition import CompositionRoot
from app.infrastructure.job_queue import cola_trabajos
from app.infrastructure.security_logging import log_seguridad


class IngestKnowledgeRequest(BaseModel):
    title: str = Field(min_length=1, max_length=DocumentoConocimiento.LONGITUD_MAXIMA_TITULO)
    topic: str = Field(min_length=1, max_length=DocumentoConocimiento.LONGITUD_MAXIMA_TEMA)
    content: str = Field(min_length=1, max_length=DocumentoConocimiento.LONGITUD_MAXIMA_CONTENIDO)


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


class AsyncJobAcceptedResponse(BaseModel):
    job_id: str
    status: str
    job_type: str


def _documento_response(resultado: ResultadoDocumentoConocimiento) -> KnowledgeDocumentResponse:
    return KnowledgeDocumentResponse(
        id=resultado.id,
        title=resultado.titulo,
        topic=resultado.tema,
        source_path=resultado.ruta_origen,
        content_hash=resultado.hash_contenido,
        chunk_count=resultado.cantidad_fragmentos,
        ingested_at=resultado.incorporado_en,
        status=resultado.estado,
    )


def create_knowledge_router(container: CompositionRoot) -> APIRouter:
    router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])
    require_authenticated_farmer = dependencia_agricultor_autenticado(container)
    require_knowledge_writer = dependencia_escritura_conocimiento(container)

    @router.post(
        "/ingest",
        status_code=status.HTTP_201_CREATED,
        response_model=KnowledgeDocumentResponse,
    )
    def ingest_knowledge(
        payload: IngestKnowledgeRequest,
        farmer_id: str = Depends(require_knowledge_writer),
    ) -> KnowledgeDocumentResponse:
        command = ComandoIncorporarConocimiento(
            titulo=payload.title,
            tema=payload.topic,
            contenido=payload.content,
        )
        try:
            result = container.puerto_incorporar_conocimiento.ejecutar(command)
        except ErrorDocumentoConocimientoDuplicado as error:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(error),
            ) from error
        except ErrorDocumentoConocimientoInvalido as error:
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
            "knowledge_ingest",
            habilitado=container.settings.security_log_enabled,
            farmer_id=farmer_id,
            document_id=result.id,
        )
        return _documento_response(result)

    @router.post("/index", response_model=IndexKnowledgeResponse)
    def index_knowledge(
        farmer_id: str = Depends(require_knowledge_writer),
    ) -> IndexKnowledgeResponse:
        try:
            result = container.puerto_indexar_conocimiento.ejecutar()
        except ErrorArchivoConocimientoNoEncontrado as error:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(error),
            ) from error
        except ErrorDominio as error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error),
            ) from error
        log_seguridad(
            "knowledge_index",
            habilitado=container.settings.security_log_enabled,
            farmer_id=farmer_id,
            indexed=result.documentos_indexados,
        )
        return IndexKnowledgeResponse(
            indexed_documents=result.documentos_indexados,
            total_chunks=result.total_fragmentos,
            collection=container.settings.chroma_collection,
            documents=[_documento_response(item) for item in result.documentos],
        )

    @router.post(
        "/index/async",
        status_code=status.HTTP_202_ACCEPTED,
        response_model=AsyncJobAcceptedResponse,
    )
    def index_knowledge_async(
        farmer_id: str = Depends(require_knowledge_writer),
    ) -> AsyncJobAcceptedResponse:
        if not container.settings.async_jobs_enabled:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Cola asíncrona deshabilitada. Use POST /api/v1/knowledge/index.",
            )

        def _worker() -> dict:
            result = container.puerto_indexar_conocimiento.ejecutar()
            log_seguridad(
                "knowledge_index_async",
                habilitado=container.settings.security_log_enabled,
                farmer_id=farmer_id,
                indexed=result.documentos_indexados,
            )
            return {
                "indexed_documents": result.documentos_indexados,
                "total_chunks": result.total_fragmentos,
                "collection": container.settings.chroma_collection,
                "documents": [
                    _documento_response(item).model_dump() for item in result.documentos
                ],
            }

        job = cola_trabajos.enqueue(
            "knowledge_index",
            _worker,
            farmer_id=farmer_id,
        )
        return AsyncJobAcceptedResponse(
            job_id=job.id,
            status=job.status.value,
            job_type=job.job_type,
        )

    @router.get("/documents", response_model=list[KnowledgeDocumentResponse])
    def list_knowledge_documents(
        _farmer_id: str = Depends(require_authenticated_farmer),
    ) -> list[KnowledgeDocumentResponse]:
        results = container.puerto_listar_documentos_conocimiento.ejecutar()
        return [_documento_response(item) for item in results]

    return router
