from sqlalchemy import DateTime, String, Text, select
from sqlalchemy.orm import Mapped, mapped_column, sessionmaker

from app.domain.entities.consulta import Consulta
from app.domain.entities.contexto_agricola import ContextoAgricola
from app.domain.entities.respuesta import Respuesta
from app.domain.ports.output.repositorio_consulta_port import PuertoRepositorioConsulta
from app.domain.valueObjects.cultivo import Cultivo
from app.domain.valueObjects.region import Region
from app.infrastructure.adapters.output.mysql.connection import Base
from app.infrastructure.adapters.output.mysql.repositorio_contexto_agricola import (
    RegistroContextoAgricola,
)


class RegistroConsulta(Base):
    __tablename__ = "queries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    farmer_id: Mapped[str] = mapped_column(String(36), nullable=False)
    context_id: Mapped[str] = mapped_column(String(36), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime, nullable=False)


class RegistroRespuesta(Base):
    __tablename__ = "responses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    query_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False)
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    generation_method: Mapped[str] = mapped_column(String(40), nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime, nullable=False)


class RepositorioConsultaMysql(PuertoRepositorioConsulta):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    def buscar_contexto_seleccionado(self, agricultor_id: str) -> ContextoAgricola | None:
        with self._session_factory() as session:
            registro = session.scalar(
                select(RegistroContextoAgricola).where(
                    RegistroContextoAgricola.farmer_id == agricultor_id,
                    RegistroContextoAgricola.is_selected.is_(True),
                )
            )
            if registro is None:
                return None
            return ContextoAgricola(
                contexto_id=registro.id,
                agricultor_id=registro.farmer_id,
                nombre_predio=registro.plot_name,
                cultivo=Cultivo(registro.crop),
                region=Region(registro.region),
                observaciones=registro.notes,
                esta_seleccionado=bool(registro.is_selected),
                creado_en=registro.created_at,
            )

    def guardar_consulta(self, consulta: Consulta) -> None:
        registro = RegistroConsulta(
            id=consulta.id,
            farmer_id=consulta.agricultor_id,
            context_id=consulta.contexto_id,
            question_text=consulta.texto.value,
            created_at=consulta.creado_en,
        )
        with self._session_factory() as session:
            session.add(registro)
            session.commit()

    def guardar_respuesta(self, respuesta: Respuesta) -> None:
        registro = RegistroRespuesta(
            id=respuesta.id,
            query_id=respuesta.consulta_id,
            answer_text=respuesta.texto_respuesta,
            generation_method=respuesta.metodo_generacion,
            created_at=respuesta.creado_en,
        )
        with self._session_factory() as session:
            session.add(registro)
            session.commit()
