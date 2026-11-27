import json
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.infrastructure.adapters.input.http.dependencia_autenticacion import (
    dependencia_administrador_autenticado,
)
from app.domain.exceptions import (
    ErrorDocumentoConocimientoDuplicado,
    ErrorDocumentoConocimientoInvalido,
)
from app.domain.ports.input.incorporar_conocimiento_port import (
    ComandoIncorporarConocimiento,
)
from app.domain.valueObjects.hash_contenido import HashContenido
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


class AdminRegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=150)
    password: str = Field(min_length=12, max_length=72)

    @field_validator("password")
    @classmethod
    def validate_bcrypt_password_size(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("La contraseña no debe superar 72 bytes.")
        return value


class AdminRegisterResponse(BaseModel):
    name: str
    email: str


def create_admin_router(container: CompositionRoot) -> APIRouter:
    router = APIRouter(prefix="/api/v1/admin", tags=["administration"])
    current_admin = dependencia_administrador_autenticado(container)

    @router.post(
        "/auth/register",
        status_code=status.HTTP_201_CREATED,
        response_model=AdminRegisterResponse,
    )
    def register_admin(payload: AdminRegisterRequest) -> AdminRegisterResponse:
        name = payload.name.strip()
        email = payload.email.strip().lower()

        if not name:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="El nombre es obligatorio.",
            )

        if email.count("@") != 1 or "." not in email.rsplit("@", 1)[-1]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Ingresa un correo electrónico válido.",
            )

        password_hash = container.puerto_hasher_contrasena.hashear_contrasena(
            payload.password
        )

        try:
            with container.session_factory() as session:
                existing_admin = session.execute(
                    text("SELECT id FROM administradores LIMIT 1")
                ).first()

                if existing_admin:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=(
                            "El registro público ya está cerrado porque existe "
                            "un administrador."
                        ),
                    )

                session.execute(
                    text("""
                        INSERT INTO administradores (
                            nombre,
                            correo,
                            contrasena_hash,
                            activo
                        )
                        VALUES (
                            :name,
                            :email,
                            :password_hash,
                            1
                        )
                    """),
                    {
                        "name": name,
                        "email": email,
                        "password_hash": password_hash,
                    },
                )
                session.commit()
        except IntegrityError as error:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe una cuenta con ese correo.",
            ) from error

        return AdminRegisterResponse(name=name, email=email)

    def obtener_documento(session, document_id: int):
        return session.execute(
            text("""
                SELECT
                    d.id,
                    d.ruta_origen,
                    d.hash_contenido,
                    d.fecha_creacion,
                    COALESCE(a.titulo, '') AS titulo,
                    COALESCE(a.tema, '') AS tema,
                    COALESCE(a.estado, 'ACTIVO') AS estado,
                    COALESCE(a.version, 1) AS version,
                    a.fecha_actualizacion
                FROM documentos_conocimiento AS d
                LEFT JOIN documentos_conocimiento_administracion AS a
                    ON a.documento_id = d.id
                WHERE d.id = :document_id
                LIMIT 1
            """),
            {"document_id": document_id},
        ).mappings().first()

    def guardar_metadata(
        session,
        documento_id: int,
        titulo: str,
        tema: str,
    ) -> None:
        session.execute(
            text("""
                INSERT INTO documentos_conocimiento_administracion (
                    documento_id,
                    titulo,
                    tema,
                    estado,
                    version
                )
                VALUES (
                    :documento_id,
                    :titulo,
                    :tema,
                    'ACTIVO',
                    1
                )
                ON DUPLICATE KEY UPDATE
                    titulo = VALUES(titulo),
                    tema = VALUES(tema)
            """),
            {
                "documento_id": documento_id,
                "titulo": titulo[:200],
                "tema": tema[:50],
            },
        )

    @router.post("/auth/login", response_model=AdminLoginResponse)
    def login(payload: AdminLoginRequest) -> AdminLoginResponse:
        email = str(payload.email).strip().lower()

        with container.session_factory() as session:
            registro = session.execute(
                text("""
                    SELECT id, nombre, correo, contrasena_hash
                    FROM administradores
                    WHERE correo = :correo
                      AND activo = 1
                    LIMIT 1
                """),
                {"correo": email},
            ).mappings().first()

        if not registro or not container.puerto_hasher_contrasena.verificar_contrasena(
            payload.password,
            str(registro["contrasena_hash"]),
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales inválidas",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = container.puerto_emisor_token.emitir_token(
            sujeto=str(registro["id"]),
            claims={"email": email, "rol": "ADMINISTRADOR"},
        )

        return AdminLoginResponse(
            access_token=token,
            name=str(registro["nombre"]),
            email=email,
        )

    @router.get("/metrics")
    def metrics(
        days: int = Query(default=30, ge=1, le=365),
        _admin_id: str = Depends(current_admin),
    ) -> dict[str, object]:
        with container.session_factory() as session:
            summary = session.execute(
                text("""
                    SELECT
                        COUNT(*) AS total_solicitudes,
                        SUM(
                            CASE WHEN codigo_respuesta < 400 THEN 1 ELSE 0 END
                        ) AS consultas_atendidas,
                        SUM(
                            CASE WHEN codigo_respuesta >= 400 THEN 1 ELSE 0 END
                        ) AS solicitudes_con_error,
                        AVG(duracion_ms) AS promedio_ms,
                        MAX(duracion_ms) AS maximo_ms
                    FROM metricas_consulta
                    WHERE fecha_creacion >= DATE_SUB(
                        CURRENT_TIMESTAMP,
                        INTERVAL :days DAY
                    )
                """),
                {"days": days},
            ).mappings().first() or {}

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
        base_dir = Path(container.settings.knowledge_dir)

        with container.session_factory() as session:
            rows = session.execute(
                text("""
                    SELECT
                        d.id,
                        d.ruta_origen,
                        d.hash_contenido,
                        d.fecha_creacion,
                        COALESCE(a.titulo, '') AS titulo,
                        COALESCE(a.tema, '') AS tema,
                        COALESCE(a.estado, 'ACTIVO') AS estado,
                        COALESCE(a.version, 1) AS version,
                        a.fecha_actualizacion
                    FROM documentos_conocimiento AS d
                    LEFT JOIN documentos_conocimiento_administracion AS a
                        ON a.documento_id = d.id
                    ORDER BY d.fecha_creacion DESC, d.id DESC
                """)
            ).mappings().all()

            result = []

            for row in rows:
                source = str(row["ruta_origen"] or "")
                meta_path = (
                    base_dir / Path(source).name
                ).with_suffix(".meta.json")

                metadata = {}
                if meta_path.is_file():
                    try:
                        value = json.loads(meta_path.read_text(encoding="utf-8"))
                        metadata = value if isinstance(value, dict) else {}
                    except (OSError, ValueError):
                        metadata = {}

                title = str(row["titulo"] or metadata.get("title") or "").strip()
                topic = str(row["tema"] or metadata.get("topic") or "").strip()

                if title or topic:
                    guardar_metadata(
                        session,
                        int(row["id"]),
                        title,
                        topic,
                    )

                result.append({
                    "id": str(row["id"]),
                    "title": title or "Documento sin título",
                    "topic": topic or "Sin tema",
                    "source_path": source,
                    "content_hash": str(row["hash_contenido"]),
                    "status": str(row["estado"]),
                    "version": int(row["version"]),
                    "created_at": str(row["fecha_creacion"] or ""),
                    "updated_at": str(row["fecha_actualizacion"] or ""),
                })

            session.commit()

        return result

    @router.get("/documents/{document_id}")
    def get_document(
        document_id: int,
        _admin_id: str = Depends(current_admin),
    ) -> dict[str, object]:
        with container.session_factory() as session:
            row = obtener_documento(session, document_id)

        if row is None:
            raise HTTPException(status_code=404, detail="Documento no encontrado")

        source = str(row["ruta_origen"] or "")
        target = Path(container.settings.knowledge_dir) / Path(source).name

        if not target.is_file():
            raise HTTPException(
                status_code=409,
                detail="No se encontró el archivo del documento.",
            )

        metadata_path = target.with_suffix(".meta.json")
        metadata = {}

        if metadata_path.is_file():
            try:
                value = json.loads(metadata_path.read_text(encoding="utf-8"))
                metadata = value if isinstance(value, dict) else {}
            except (OSError, ValueError):
                metadata = {}

        return {
            "id": str(row["id"]),
            "title": str(row["titulo"] or metadata.get("title") or ""),
            "topic": str(row["tema"] or metadata.get("topic") or ""),
            "content": target.read_text(encoding="utf-8"),
            "status": str(row["estado"]),
            "version": int(row["version"]),
        }

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

            with container.session_factory() as session:
                guardar_metadata(
                    session,
                    int(result.id),
                    result.titulo,
                    result.tema,
                )
                session.commit()

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
        content_value = payload.content.strip()

        if not content_value:
            raise HTTPException(
                status_code=400,
                detail="El contenido es obligatorio.",
            )

        with container.session_factory() as session:
            row = obtener_documento(session, document_id)

            if row is None:
                raise HTTPException(
                    status_code=404,
                    detail="Documento no encontrado",
                )

            if str(row["estado"]) == "INACTIVO":
                raise HTTPException(
                    status_code=409,
                    detail="No se puede actualizar un documento inactivo.",
                )

            source = str(row["ruta_origen"])
            target = Path(container.settings.knowledge_dir) / Path(source).name

            if not target.is_file():
                raise HTTPException(
                    status_code=409,
                    detail="No se encontró el archivo del documento.",
                )

            content_hash = HashContenido.desde_contenido(content_value)

            duplicado = session.execute(
                text("""
                    SELECT id
                    FROM documentos_conocimiento
                    WHERE hash_contenido = :hash
                      AND id <> :document_id
                    LIMIT 1
                """),
                {
                    "hash": content_hash.value,
                    "document_id": document_id,
                },
            ).first()

            if duplicado:
                raise HTTPException(
                    status_code=409,
                    detail="El contenido ya está registrado en otro documento.",
                )

            session.execute(
                text("""
                    UPDATE documentos_conocimiento
                    SET hash_contenido = :hash
                    WHERE id = :document_id
                """),
                {
                    "hash": content_hash.value,
                    "document_id": document_id,
                },
            )

            session.execute(
                text("""
                    INSERT INTO documentos_conocimiento_administracion (
                        documento_id,
                        titulo,
                        tema,
                        estado,
                        version
                    )
                    VALUES (
                        :documento_id,
                        :titulo,
                        :tema,
                        'ACTIVO',
                        2
                    )
                    ON DUPLICATE KEY UPDATE
                        titulo = VALUES(titulo),
                        tema = VALUES(tema),
                        version = version + 1
                """),
                {
                    "documento_id": document_id,
                    "titulo": payload.title.strip(),
                    "tema": payload.topic.strip(),
                },
            )

            session.commit()

        target.write_text(content_value, encoding="utf-8")
        metadata_path = target.with_suffix(".meta.json")
        metadata_path.write_text(
            json.dumps(
                {
                    "title": payload.title.strip(),
                    "topic": payload.topic.strip(),
                    "chunk_count": 0,
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        container.puerto_almacen_vectores.delete_by_document(str(document_id))
        indexed = container.puerto_indexar_conocimiento.ejecutar()

        with container.session_factory() as session:
            updated = obtener_documento(session, document_id)

        return {
            "id": str(document_id),
            "title": payload.title.strip(),
            "topic": payload.topic.strip(),
            "status": str(updated["estado"]),
            "version": int(updated["version"]),
            "indexed_chunks": indexed.total_fragmentos,
        }

    @router.patch("/documents/{document_id}/status")
    def update_document_status(
        document_id: int,
        payload: AdminDocumentStateRequest,
        _admin_id: str = Depends(current_admin),
    ) -> dict[str, object]:
        with container.session_factory() as session:
            row = obtener_documento(session, document_id)

            if row is None:
                raise HTTPException(
                    status_code=404,
                    detail="Documento no encontrado",
                )

            session.execute(
                text("""
                    INSERT INTO documentos_conocimiento_administracion (
                        documento_id,
                        titulo,
                        tema,
                        estado,
                        version
                    )
                    VALUES (
                        :documento_id,
                        :titulo,
                        :tema,
                        :estado,
                        1
                    )
                    ON DUPLICATE KEY UPDATE
                        estado = VALUES(estado)
                """),
                {
                    "documento_id": document_id,
                    "titulo": str(row["titulo"] or ""),
                    "tema": str(row["tema"] or ""),
                    "estado": payload.status,
                },
            )

            session.commit()

        if payload.status == "INACTIVO":
            container.puerto_almacen_vectores.delete_by_document(str(document_id))
        else:
            container.puerto_indexar_conocimiento.ejecutar()

        return {
            "documento_id": document_id,
            "estado": payload.status,
        }

    @router.get("/evaluations")
    def list_evaluations(
        _admin_id: str = Depends(current_admin),
    ) -> list[dict[str, object]]:
        with container.session_factory() as session:
            rows = session.execute(
                text("""
                    SELECT
                        id,
                        dataset_version,
                        proveedor,
                        modelo,
                        precision_promedio,
                        pertinencia_promedio,
                        fidelidad_promedio,
                        recall_contexto_promedio,
                        duracion_promedio_ms,
                        total_muestras,
                        fecha_creacion
                    FROM evaluaciones_ia
                    ORDER BY fecha_creacion DESC, id DESC
                """)
            ).mappings().all()

        return [
            {
                "id": str(row["id"]),
                "dataset_version": str(row["dataset_version"]),
                "provider": str(row["proveedor"]),
                "model": str(row["modelo"]),
                "retrieval_precision": float(row["precision_promedio"] or 0),
                "answer_pertinence": float(row["pertinencia_promedio"] or 0),
                "faithfulness": (
                    float(row["fidelidad_promedio"])
                    if row["fidelidad_promedio"] is not None else None
                ),
                "context_recall": (
                    float(row["recall_contexto_promedio"])
                    if row["recall_contexto_promedio"] is not None else None
                ),
                "average_response_ms": float(row["duracion_promedio_ms"] or 0),
                "sample_count": int(row["total_muestras"] or 0),
                "created_at": str(row["fecha_creacion"] or ""),
            }
            for row in rows
        ]

    @router.get("/evaluations/{evaluation_id}/details")
    def evaluation_details(
        evaluation_id: int,
        _admin_id: str = Depends(current_admin),
    ) -> list[dict[str, object]]:
        with container.session_factory() as session:
            rows = session.execute(
                text("""
                    SELECT
                        id,
                        evaluacion_id,
                        item_id,
                        pregunta,
                        precision_score,
                        pertinencia,
                        duracion_ms,
                        respuesta
                    FROM evaluaciones_ia_detalle
                    WHERE evaluacion_id = :evaluation_id
                    ORDER BY id ASC
                """),
                {"evaluation_id": evaluation_id},
            ).mappings().all()

        return [
            {
                "id": str(row["id"]),
                "evaluation_id": str(row["evaluacion_id"]),
                "item_id": str(row["item_id"]),
                "question": str(row["pregunta"]),
                "precision": (
                    float(row["precision_score"])
                    if row["precision_score"] is not None else None
                ),
                "pertinence": (
                    float(row["pertinencia"])
                    if row["pertinencia"] is not None else None
                ),
                "duration_ms": float(row["duracion_ms"] or 0),
                "answer": str(row["respuesta"]),
            }
            for row in rows
        ]

    return router
