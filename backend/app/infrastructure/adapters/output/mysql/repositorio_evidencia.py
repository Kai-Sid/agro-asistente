from decimal import Decimal

from sqlalchemy import Integer, Numeric, String, Text, select
from sqlalchemy.orm import Mapped, mapped_column, sessionmaker

from app.domain.entities.evidencia import Evidencia
from app.domain.ports.output.repositorio_evidencia_port import PuertoRepositorioEvidencia
from app.infrastructure.adapters.output.mysql.connection import Base


class RegistroEvidencia(Base):
    __tablename__ = "evidences"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    query_id: Mapped[str] = mapped_column(String(36), nullable=False)
    response_id: Mapped[str] = mapped_column(String(36), nullable=False)
    document_id: Mapped[str] = mapped_column(String(36), nullable=False)
    chroma_chunk_id: Mapped[str] = mapped_column(String(120), nullable=False)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    similarity_score: Mapped[Decimal] = mapped_column(Numeric(6, 5), nullable=False)
    rank_order: Mapped[int] = mapped_column(Integer, nullable=False)


class RepositorioEvidenciaMysql(PuertoRepositorioEvidencia):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    def guardar_todas(self, evidencias: list[Evidencia]) -> None:
        if not evidencias:
            return
        registros = [
            RegistroEvidencia(
                id=item.id,
                query_id=item.consulta_id,
                response_id=item.respuesta_id,
                document_id=item.documento_id,
                chroma_chunk_id=item.fragmento_id,
                excerpt=item.extracto,
                similarity_score=Decimal(str(item.puntaje_similitud)),
                rank_order=item.orden_relevancia,
            )
            for item in evidencias
        ]
        with self._session_factory() as session:
            session.add_all(registros)
            session.commit()

    def listar_por_consulta_id(self, consulta_id: str) -> list[Evidencia]:
        with self._session_factory() as session:
            registros = session.scalars(
                select(RegistroEvidencia)
                .where(RegistroEvidencia.query_id == consulta_id)
                .order_by(RegistroEvidencia.rank_order.asc())
            ).all()
            return [self._a_entidad(registro) for registro in registros]

    def _a_entidad(self, registro: RegistroEvidencia) -> Evidencia:
        return Evidencia(
            evidencia_id=registro.id,
            consulta_id=registro.query_id,
            respuesta_id=registro.response_id,
            documento_id=registro.document_id,
            fragmento_id=registro.chroma_chunk_id,
            extracto=registro.excerpt,
            puntaje_similitud=float(registro.similarity_score),
            orden_relevancia=int(registro.rank_order),
        )
