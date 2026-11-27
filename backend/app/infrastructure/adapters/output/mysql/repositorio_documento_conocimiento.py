import json
from pathlib import Path

import pymysql.err
from sqlalchemy import DateTime, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, sessionmaker

from app.domain.entities.documento_conocimiento import DocumentoConocimiento
from app.domain.exceptions import (
    ErrorArchivoConocimientoNoEncontrado,
    ErrorDocumentoConocimientoDuplicado,
)
from app.domain.ports.output.repositorio_documento_conocimiento_port import (
    PuertoRepositorioDocumentoConocimiento,
)
from app.domain.valueObjects.hash_contenido import HashContenido
from app.infrastructure.adapters.output.mysql.connection import (
    Base,
    id_a_dominio,
    id_a_entero,
)


class RegistroDocumentoConocimiento(Base):
    __tablename__ = "documentos_conocimiento"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ruta_origen: Mapped[str] = mapped_column(String(500), nullable=False)
    hash_contenido: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    fecha_creacion: Mapped[object] = mapped_column(DateTime, nullable=True)


class RepositorioDocumentoConocimientoMysql(PuertoRepositorioDocumentoConocimiento):
    def __init__(self, session_factory: sessionmaker, knowledge_dir: str) -> None:
        self._session_factory = session_factory
        self._directorio_conocimiento = Path(knowledge_dir)

    def existe_por_hash(self, hash_contenido: HashContenido) -> bool:
        with self._session_factory() as session:
            resultado = session.execute(
                text("""
                    SELECT EXISTS(
                        SELECT 1
                        FROM documentos_conocimiento
                        WHERE hash_contenido = :hash_contenido
                    ) AS existe
                """),
                {"hash_contenido": hash_contenido.value},
            ).scalar_one()

            return bool(resultado)

    def guardar(self, documento: DocumentoConocimiento, contenido: str) -> None:
        ruta_archivo = self._ruta_archivo(documento.ruta_origen)
        ruta_meta = self._ruta_meta(documento.ruta_origen)

        ruta_archivo.parent.mkdir(parents=True, exist_ok=True)
        ruta_archivo.write_text(contenido, encoding="utf-8")

        _escribir_meta(
            ruta_meta,
            titulo=documento.titulo,
            tema=documento.tema,
            cantidad_fragmentos=documento.cantidad_fragmentos,
        )

        try:
            with self._session_factory() as session:
                resultado = session.execute(
                    text("""
                        INSERT INTO documentos_conocimiento (
                            ruta_origen,
                            hash_contenido,
                            fecha_creacion
                        )
                        VALUES (
                            :ruta_origen,
                            :hash_contenido,
                            :fecha_creacion
                        )
                    """),
                    {
                        "ruta_origen": documento.ruta_origen[:500],
                        "hash_contenido": documento.hash_contenido.value,
                        "fecha_creacion": documento.incorporado_en,
                    },
                )

                documento.id = id_a_dominio(resultado.lastrowid)
                session.commit()

        except pymysql.err.IntegrityError as error:
            ruta_archivo.unlink(missing_ok=True)
            ruta_meta.unlink(missing_ok=True)

            if error.args and error.args[0] == 1062:
                raise ErrorDocumentoConocimientoDuplicado(
                    "El documento de conocimiento ya está registrado"
                ) from error

            raise

        except Exception:
            ruta_archivo.unlink(missing_ok=True)
            ruta_meta.unlink(missing_ok=True)
            raise

    def listar_todos(self) -> list[DocumentoConocimiento]:
        with self._session_factory() as session:
            registros = session.execute(
                text("""
                    SELECT
                        d.id,
                        d.ruta_origen,
                        d.hash_contenido,
                        d.fecha_creacion
                    FROM documentos_conocimiento AS d
                    LEFT JOIN documentos_conocimiento_administracion AS a
                        ON a.documento_id = d.id
                    WHERE COALESCE(a.estado, 'ACTIVO') = 'ACTIVO'
                    ORDER BY d.fecha_creacion DESC, d.id DESC
                """)
            ).mappings().all()

            return [
                self._a_entidad(dict(registro))
                for registro in registros
            ]

    def buscar_por_id(self, documento_id: str) -> DocumentoConocimiento | None:
        with self._session_factory() as session:
            registro = session.execute(
                text("""
                    SELECT
                        id,
                        ruta_origen,
                        hash_contenido,
                        fecha_creacion
                    FROM documentos_conocimiento
                    WHERE id = :documento_id
                    LIMIT 1
                """),
                {"documento_id": id_a_entero(documento_id)},
            ).mappings().first()

            return self._a_entidad(dict(registro)) if registro else None

    def leer_contenido(self, documento: DocumentoConocimiento) -> str:
        ruta_archivo = self._ruta_archivo(documento.ruta_origen)

        if not ruta_archivo.exists():
            raise ErrorArchivoConocimientoNoEncontrado(
                "No se encontró el archivo del documento de conocimiento"
            )

        return ruta_archivo.read_text(encoding="utf-8")

    def actualizar_cantidad_fragmentos(
        self, documento_id: str, cantidad_fragmentos: int
    ) -> None:
        documento = self.buscar_por_id(documento_id)

        if documento is None:
            return

        meta = _leer_meta(self._ruta_meta(documento.ruta_origen))

        _escribir_meta(
            self._ruta_meta(documento.ruta_origen),
            titulo=str(meta.get("title") or ""),
            tema=str(meta.get("topic") or ""),
            cantidad_fragmentos=cantidad_fragmentos,
        )

    def _ruta_archivo(self, ruta_origen: str) -> Path:
        return self._directorio_conocimiento / Path(ruta_origen).name

    def _ruta_meta(self, ruta_origen: str) -> Path:
        return self._ruta_archivo(ruta_origen).with_suffix(".meta.json")

    def _a_entidad(self, registro: dict[str, object]) -> DocumentoConocimiento:
        ruta_origen = str(registro["ruta_origen"])
        meta = _leer_meta(self._ruta_meta(ruta_origen))

        return DocumentoConocimiento(
            documento_id=id_a_dominio(registro["id"]),
            titulo=str(meta.get("title") or ""),
            ruta_origen=ruta_origen,
            tema=str(meta.get("topic") or ""),
            hash_contenido=HashContenido(str(registro["hash_contenido"])),
            cantidad_fragmentos=int(meta.get("chunk_count") or 0),
            incorporado_en=registro["fecha_creacion"],
        )


def _escribir_meta(
    ruta: Path,
    titulo: str,
    tema: str,
    cantidad_fragmentos: int,
) -> None:
    ruta.write_text(
        json.dumps(
            {
                "title": titulo,
                "topic": tema,
                "chunk_count": cantidad_fragmentos,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def _leer_meta(ruta: Path) -> dict[str, object]:
    if not ruta.exists():
        return {}

    try:
        loaded = json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}

    return loaded if isinstance(loaded, dict) else {}
