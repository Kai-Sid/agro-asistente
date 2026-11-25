import json
from pathlib import Path
from typing import Literal

import pymysql.err
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.infrastructure.adapters.input.http.dependencia_autenticacion import (
    dependencia_administrador_autenticado,
)
from app.domain.exceptions import ErrorDocumentoConocimientoDuplicado, ErrorDocumentoConocimientoInvalido
from app.domain.ports.input.incorporar_conocimiento_port import ComandoIncorporarConocimiento
from app.domain.valueObjects.hash_contenido import HashContenido
from app.infrastructure.adapters.output.mysql.procedures import MysqlStoredProcedureGateway
from app.infrastructure.composition import CompositionRoot


class AdminLoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=150)
    password: str = Field(min_length=1)


class AdminDocumentRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    topic: str = Field(min_length=1, max_length=50)
    content: str = Field(min_length=1, max_length=20000)


class AdminDocumentStateRequest(BaseModel):
    status: Literal["ACTIVO", "INACTIVO"]


class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str = "ADMINISTRADOR"
    name: str
    email: str


def create_admin_router(container: CompositionRoot) -> APIRouter:
    router = APIRouter(prefix="/api/v1/admin", tags=["administration"])
    procedures = MysqlStoredProcedureGateway(container.session_factory)
    current_admin = dependencia_administrador_autenticado(container)

    @router.post("/auth/login", response_model=AdminLoginResponse)
    def login(payload: AdminLoginRequest) -> AdminLoginResponse:
        email = str(payload.email).strip().lower()
        rows = procedures.call("sp_administrador_buscar_por_correo", (email,))
        if not rows or not container.puerto_hasher_contrasena.verificar_contrasena(
            payload.password, str(rows[0]["contrasena_hash"])
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas",
                headers={"WWW-Authenticate": "Bearer"},
            )
        admin = rows[0]
        token = container.puerto_emisor_token.emitir_token(
            sujeto=str(admin["id"]),
            claims={"email": email, "rol": "ADMINISTRADOR"},
        )
        return AdminLoginResponse(
            access_token=token,
            name=str(admin["nombre"]),
            email=email,
        )

    @router.get("/metrics")
    def metrics(
        days: int = Query(default=30, ge=1, le=365),
        _admin_id: str = Depends(current_admin),
    ) -> dict[str, object]:
        rows = procedures.call("sp_metricas_consulta_resumen", (days,))
        summary = rows[0] if rows else {}
        return {
            "days": days,
            "total_requests": int(summary.get("total_solicitudes") or 0),
            "queries_attended": int(summary.get("consultas_atendidas") or 0),
            "requests_with_error": int(summary.get("solicitudes_con_error") or 0),
            "average_response_ms": float(summary.get("promedio_ms") or 0),
            "maximum_response_ms": int(summary.get("maximo_ms") or 0),
        }


    @router.get("/documents")
    def list_documents(
        _admin_id: str = Depends(current_admin),
    ) -> list[dict[str, object]]:
        rows = procedures.call("sp_admin_documentos_listar")
        result: list[dict[str, object]] = []
        base_dir = Path(container.settings.knowledge_dir)
        for row in rows:
            source = str(row.get("ruta_origen") or "")
            meta_path = base_dir / Path(source).name
            meta_path = meta_path.with_suffix(".meta.json")
            metadata: dict[str, object] = {}
            if meta_path.is_file():
                try:
                    value = json.loads(meta_path.read_text(encoding="utf-8"))
                    metadata = value if isinstance(value, dict) else {}
                except (OSError, ValueError):
                    metadata = {}
            title = str(row.get("titulo") or metadata.get("title") or "").strip()
            topic = str(row.get("tema") or metadata.get("topic") or "").strip()
            if title or topic:
                procedures.call(
                    "sp_admin_documento_metadata_asegurar",
                    (int(row["id"]), title, topic),
                )
            result.append(
                {
                    "id": str(row["id"]),
                    "title": title or "Documento sin título",
                    "topic": topic or "Sin tema",
                    "source_path": source,
                    "content_hash": str(row["hash_contenido"]),
                    "status": str(row.get("estado") or "ACTIVO"),
                    "version": int(row.get("version") or 1),
                    "created_at": str(row.get("fecha_creacion") or ""),
                    "updated_at": str(row.get("fecha_actualizacion") or ""),
                }
            )
        return result

    @router.post("/documents", status_code=status.HTTP_201_CREATED)
    def create_document(
        payload: AdminDocumentRequest,
        _admin_id: str = Depends(current_admin),
    ) -> dict[str, object]:
        try:
            result = container.puerto_incorporar_conocimiento.ejecutar(
                ComandoIncorporarConocimiento(
                    titulo=payload.title,
                    tema=payload.topic,
                    contenido=payload.content,
                )
            )
            procedures.call(
                "sp_admin_documento_metadata_asegurar",
                (int(result.id), result.titulo, result.tema),
            )
            indexed = container.puerto_indexar_conocimiento.ejecutar()
        except ErrorDocumentoConocimientoDuplicado as error:
            raise HTTPException(status_code=409, detail=str(error)) from error
        except ErrorDocumentoConocimientoInvalido as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except Exception as error:
            raise HTTPException(
                status_code=503,
                detail="El documento se guardó, pero no se pudo completar su indexación.",
            ) from error
        return {
            "id": result.id,
            "title": result.titulo,
            "topic": result.tema,
            "status": "ACTIVO",
            "version": 1,
            "indexed_chunks": indexed.total_fragmentos,
        }

    @router.put("/documents/{document_id}")
    def update_document(
        document_id: int,
        payload: AdminDocumentRequest,
        _admin_id: str = Depends(current_admin),
    ) -> dict[str, object]:
        rows = procedures.call("sp_admin_documentos_listar")
        row = next((item for item in rows if int(item["id"]) == document_id), None)
        if row is None:
            raise HTTPException(status_code=404, detail="Documento no encontrado")
        content_value = payload.content.strip()
        if not content_value:
            raise HTTPException(status_code=400, detail="El contenido es obligatorio.")
        source = str(row["ruta_origen"])
        target = Path(container.settings.knowledge_dir) / Path(source).name
        if not target.is_file():
            raise HTTPException(status_code=409, detail="No se encontró el archivo del documento.")
        content_hash = HashContenido.desde_contenido(content_value)
        try:
            updated = procedures.call(
                "sp_admin_documento_contenido_actualizar",
                (document_id, content_hash.value, payload.title.strip(), payload.topic.strip()),
            )
        except pymysql.err.MySQLError as error:
            if error.args and error.args[0] == 1644:
                raise HTTPException(status_code=409, detail=str(error.args[-1])) from error
            raise
        target.write_text(content_value, encoding="utf-8")
        metadata_path = target.with_suffix(".meta.json")
        metadata_path.write_text(
            json.dumps(
                {"title": payload.title.strip(), "topic": payload.topic.strip(), "chunk_count": 0},
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        container.puerto_almacen_vectores.delete_by_document(str(document_id))
        indexed = container.puerto_indexar_conocimiento.ejecutar()
        data = updated[0] if updated else {}
        return {
            "id": str(document_id),
            "title": payload.title.strip(),
            "topic": payload.topic.strip(),
            "status": str(data.get("estado") or row.get("estado") or "ACTIVO"),
            "version": int(data.get("version") or int(row.get("version") or 1) + 1),
            "indexed_chunks": indexed.total_fragmentos,
        }

    @router.patch("/documents/{document_id}/status")
    def update_document_status(
        document_id: int,
        payload: AdminDocumentStateRequest,
        _admin_id: str = Depends(current_admin),
    ) -> dict[str, object]:
        try:
            rows = procedures.call(
                "sp_admin_documento_estado_actualizar",
                (document_id, payload.status),
            )
        except pymysql.err.MySQLError as error:
            if error.args and error.args[0] == 1644:
                raise HTTPException(status_code=404, detail="Documento no encontrado") from error
            raise
        if payload.status == "INACTIVO":
            container.puerto_almacen_vectores.delete_by_document(str(document_id))
        else:
            container.puerto_indexar_conocimiento.ejecutar()
        return rows[0] if rows else {"documento_id": document_id, "estado": payload.status}

    return router
