from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.application.services.referencia_origen import resolver_referencia_documento
from app.domain.exceptions import (
    ErrorContextoSeleccionadoNoEncontrado,
    ErrorDominio,
    ErrorGeneracionTexto,
    ErrorTextoConsultaInvalido,
)
from app.domain.ports.input.registrar_consulta_port import ComandoRegistrarConsulta
from app.domain.valueObjects.texto_consulta import TextoConsulta
from app.infrastructure.adapters.input.http.dependencia_autenticacion import (
    dependencia_agricultor_autenticado,
)
from app.infrastructure.composition import CompositionRoot
from app.infrastructure.job_queue import cola_trabajos
from app.infrastructure.rate_limit import limitador_global
from app.infrastructure.security_logging import log_seguridad


class SubmitQueryRequest(BaseModel):
    text: str = Field(min_length=1, max_length=TextoConsulta.MAX_LENGTH)


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
    origin_reference: str = ""


class QueryClassificationResponse(BaseModel):
    category: str | None
    abstained: bool
    reason: str | None
    margin: float | None
    top_class: str | None
    top_score: float | None
    second_class: str | None
    second_score: float | None
    scores_are_calibrated: bool
    available: bool
    error: str | None


class SubmitQueryResponse(BaseModel):
    id: str
    text: str
    answer: str
    generation_method: str
    created_at: str
    context: QueryContextResponse
    evidences: list[QueryEvidenceResponse]
    classification: QueryClassificationResponse


class HistoryQueryResponse(BaseModel):
    id: str
    text: str
    answer: str
    generation_method: str
    created_at: str


class AsyncQueryAcceptedResponse(BaseModel):
    job_id: str
    status: str
    job_type: str


def create_query_router(container: CompositionRoot) -> APIRouter:
    router = APIRouter(prefix="/api/v1/queries", tags=["queries"])
    current_farmer_id = dependencia_agricultor_autenticado(container)

    @router.get("", response_model=list[HistoryQueryResponse])
    def list_queries(
        farmer_id: str = Depends(current_farmer_id),
        limit: int = 20,
    ) -> list[HistoryQueryResponse]:
        resultados = container.puerto_listar_consultas.ejecutar(
            agricultor_id=farmer_id,
            limite=limit,
        )
        return [
            HistoryQueryResponse(
                id=item.id,
                text=item.text,
                answer=item.answer,
                generation_method=item.generation_method,
                created_at=item.created_at,
            )
            for item in resultados
        ]

    @router.post(
        "",
        status_code=status.HTTP_201_CREATED,
        response_model=SubmitQueryResponse,
    )
    def submit_query(
        payload: SubmitQueryRequest,
        request: Request,
        farmer_id: str = Depends(current_farmer_id),
    ) -> SubmitQueryResponse:
        if container.settings.rate_limit_enabled:
            permitido = limitador_global.permitir(
                f"query:{farmer_id}",
                container.settings.rate_limit_query_max,
                container.settings.rate_limit_query_window_seconds,
            )
            if not permitido:
                log_seguridad(
                    "rate_limited",
                    habilitado=container.settings.security_log_enabled,
                    action="query",
                    farmer_id=farmer_id,
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Demasiadas consultas. Inténtalo más tarde.",
                    headers={
                        "Retry-After": str(
                            container.settings.rate_limit_query_window_seconds
                        )
                    },
                )
        del request
        command = ComandoRegistrarConsulta(agricultor_id=farmer_id, texto=payload.text)
        try:
            result = container.puerto_registrar_consulta.ejecutar(command)
        except ErrorTextoConsultaInvalido as error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error),
            ) from error
        except ErrorContextoSeleccionadoNoEncontrado as error:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(error),
            ) from error
        except ErrorGeneracionTexto as error:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(error),
            ) from error
        except ErrorDominio as error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error),
            ) from error
        return SubmitQueryResponse(
            id=result.id,
            text=result.texto,
            answer=result.respuesta,
            generation_method=result.metodo_generacion,
            created_at=result.creado_en,
            context=QueryContextResponse(
                id=result.contexto.id,
                crop=result.contexto.cultivo,
                region=result.contexto.region,
                plot_name=result.contexto.nombre_predio,
            ),
            evidences=[
                QueryEvidenceResponse(
                    document_id=item.documento_id,
                    document_title=item.titulo_documento,
                    chunk_id=item.fragmento_id,
                    excerpt=item.extracto,
                    similarity_score=item.puntaje_similitud,
                    rank_order=item.orden_relevancia,
                    origin_reference=resolver_referencia_documento(
                        container.puerto_repositorio_documento_conocimiento,
                        item.documento_id,
                    ),
                )
                for item in result.evidencias
            ],
            classification=_clasificacion_http(result),
        )

    @router.post(
        "/async",
        status_code=status.HTTP_202_ACCEPTED,
        response_model=AsyncQueryAcceptedResponse,
    )
    def submit_query_async(
        payload: SubmitQueryRequest,
        request: Request,
        farmer_id: str = Depends(current_farmer_id),
    ) -> AsyncQueryAcceptedResponse:
        if not container.settings.async_jobs_enabled:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Cola asíncrona deshabilitada. Use POST /api/v1/queries.",
            )
        if container.settings.rate_limit_enabled:
            permitido = limitador_global.permitir(
                f"query:{farmer_id}",
                container.settings.rate_limit_query_max,
                container.settings.rate_limit_query_window_seconds,
            )
            if not permitido:
                log_seguridad(
                    "rate_limited",
                    habilitado=container.settings.security_log_enabled,
                    action="query_async",
                    farmer_id=farmer_id,
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Demasiadas consultas. Inténtalo más tarde.",
                    headers={
                        "Retry-After": str(
                            container.settings.rate_limit_query_window_seconds
                        )
                    },
                )
        del request
        texto = payload.text

        def _worker() -> dict:
            command = ComandoRegistrarConsulta(agricultor_id=farmer_id, texto=texto)
            result = container.puerto_registrar_consulta.ejecutar(command)
            return {
                "id": result.id,
                "text": result.texto,
                "answer": result.respuesta,
                "generation_method": result.metodo_generacion,
                "created_at": result.creado_en,
                "context": {
                    "id": result.contexto.id,
                    "crop": result.contexto.cultivo,
                    "region": result.contexto.region,
                    "plot_name": result.contexto.nombre_predio,
                },
                "evidences": [
                    {
                        "document_id": item.documento_id,
                        "document_title": item.titulo_documento,
                        "chunk_id": item.fragmento_id,
                        "excerpt": item.extracto,
                        "similarity_score": item.puntaje_similitud,
                        "rank_order": item.orden_relevancia,
                        "origin_reference": resolver_referencia_documento(
                            container.puerto_repositorio_documento_conocimiento,
                            item.documento_id,
                        ),
                    }
                    for item in result.evidencias
                ],
                "classification": _clasificacion_http(result).model_dump(),
            }

        job = cola_trabajos.enqueue(
            "query_submit",
            _worker,
            farmer_id=farmer_id,
        )
        return AsyncQueryAcceptedResponse(
            job_id=job.id,
            status=job.status.value,
            job_type=job.job_type,
        )

    return router


def _clasificacion_http(result) -> QueryClassificationResponse:
    clasificacion = result.clasificacion
    if clasificacion is None:
        return QueryClassificationResponse(
            category=None,
            abstained=False,
            reason=None,
            margin=None,
            top_class=None,
            top_score=None,
            second_class=None,
            second_score=None,
            scores_are_calibrated=False,
            available=False,
            error=result.error_clasificacion,
        )
    return QueryClassificationResponse(
        category=clasificacion.categoria,
        abstained=clasificacion.abstencion,
        reason=clasificacion.motivo_abstencion,
        margin=clasificacion.margen,
        top_class=clasificacion.clase_primera,
        top_score=clasificacion.puntuacion_primera,
        second_class=clasificacion.clase_segunda,
        second_score=clasificacion.puntuacion_segunda,
        scores_are_calibrated=clasificacion.puntuaciones_calibradas,
        available=True,
        error=None,
    )
