from pathlib import Path

from sqlalchemy import DateTime, Integer, String, select
from sqlalchemy.exc import IntegrityError
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
from app.infrastructure.adapters.output.mysql.connection import Base


class RegistroDocumentoConocimiento(Base):
    __tablename__ = "knowledge_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    source_path: Mapped[str] = mapped_column(String(255), nullable=False)
    topic: Mapped[str] = mapped_column(String(50), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False)
    ingested_at: Mapped[object] = mapped_column(DateTime, nullable=False)


class RepositorioDocumentoConocimientoMysql(PuertoRepositorioDocumentoConocimiento):
    def __init__(self, session_factory: sessionmaker, knowledge_dir: str) -> None:
        self._session_factory = session_factory
        self._directorio_conocimiento = Path(knowledge_dir)

    def existe_por_hash(self, hash_contenido: HashContenido) -> bool:
        with self._session_factory() as session:
            documento_id = session.scalar(
                select(RegistroDocumentoConocimiento.id).where(
                    RegistroDocumentoConocimiento.content_hash == hash_contenido.value
                )
            )
            return documento_id is not None

    def guardar(self, documento: DocumentoConocimiento, contenido: str) -> None:
        ruta_archivo = self._ruta_archivo(documento.ruta_origen)
        ruta_archivo.parent.mkdir(parents=True, exist_ok=True)
        ruta_archivo.write_text(contenido, encoding="utf-8")

        registro = RegistroDocumentoConocimiento(
            id=documento.id,
            title=documento.titulo,
            source_path=documento.ruta_origen,
            topic=documento.tema,
            content_hash=documento.hash_contenido.value,
            chunk_count=documento.cantidad_fragmentos,
            ingested_at=documento.incorporado_en,
        )
        with self._session_factory() as session:
            session.add(registro)
            try:
                session.commit()
            except IntegrityError as error:
                session.rollback()
                ruta_archivo.unlink(missing_ok=True)
                raise ErrorDocumentoConocimientoDuplicado(
                    "El documento de conocimiento ya está registrado"
                ) from error

    def listar_todos(self) -> list[DocumentoConocimiento]:
        with self._session_factory() as session:
            registros = session.scalars(
                select(RegistroDocumentoConocimiento).order_by(
                    RegistroDocumentoConocimiento.ingested_at.desc()
                )
            ).all()
            return [self._a_entidad(registro) for registro in registros]

    def buscar_por_id(self, documento_id: str) -> DocumentoConocimiento | None:
        with self._session_factory() as session:
            registro = session.scalar(
                select(RegistroDocumentoConocimiento).where(
                    RegistroDocumentoConocimiento.id == documento_id
                )
            )
            if registro is None:
                return None
            return self._a_entidad(registro)

    def leer_contenido(self, documento: DocumentoConocimiento) -> str:
        ruta_archivo = self._ruta_archivo(documento.ruta_origen)
        if not ruta_archivo.exists():
            raise ErrorArchivoConocimientoNoEncontrado(
                "No se encontró el archivo del documento de conocimiento"
            )
        return ruta_archivo.read_text(encoding="utf-8")

    def actualizar_cantidad_fragmentos(self, documento_id: str, cantidad_fragmentos: int) -> None:
        with self._session_factory() as session:
            registro = session.scalar(
                select(RegistroDocumentoConocimiento).where(
                    RegistroDocumentoConocimiento.id == documento_id
                )
            )
            if registro is None:
                return
            registro.chunk_count = cantidad_fragmentos
            session.commit()

    def _ruta_archivo(self, ruta_origen: str) -> Path:
        nombre_archivo = Path(ruta_origen).name
        return self._directorio_conocimiento / nombre_archivo

    def _a_entidad(self, registro: RegistroDocumentoConocimiento) -> DocumentoConocimiento:
        return DocumentoConocimiento(
            documento_id=registro.id,
            titulo=registro.title,
            ruta_origen=registro.source_path,
            tema=registro.topic,
            hash_contenido=HashContenido(registro.content_hash),
            cantidad_fragmentos=int(registro.chunk_count),
            incorporado_en=registro.ingested_at,
        )
