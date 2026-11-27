from sqlalchemy import DateTime, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, sessionmaker

from app.domain.entities.consulta import Consulta
from app.domain.entities.contexto_agricola import ContextoAgricola
from app.domain.entities.respuesta import Respuesta
from app.domain.ports.output.repositorio_consulta_port import PuertoRepositorioConsulta
from app.domain.valueObjects.cultivo import Cultivo
from app.domain.valueObjects.region import Region
from app.infrastructure.adapters.output.mysql.connection import (
    Base,
    id_a_dominio,
    id_a_entero,
)


class RegistroConsulta(Base):
    __tablename__ = "consultas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agricultor_id: Mapped[int] = mapped_column(Integer, nullable=False)
    contexto_id: Mapped[int] = mapped_column(Integer, nullable=False)
    pregunta: Mapped[str] = mapped_column(Text, nullable=False)
    fecha_creacion: Mapped[object] = mapped_column(DateTime, nullable=True)


class RegistroRespuesta(Base):
    __tablename__ = "respuestas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    consulta_id: Mapped[int] = mapped_column(Integer, nullable=False)
    respuesta: Mapped[str] = mapped_column(Text, nullable=False)
    metodo_generacion: Mapped[str | None] = mapped_column(String(50), nullable=True)
    fecha_creacion: Mapped[object] = mapped_column(DateTime, nullable=True)


class RepositorioConsultaMysql(PuertoRepositorioConsulta):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    def buscar_contexto_seleccionado(
        self, agricultor_id: str
    ) -> ContextoAgricola | None:
        with self._session_factory() as session:
            registro = session.execute(
                text("""
                    SELECT
                        id,
                        agricultor_id,
                        nombre_parcela,
                        cultivo,
                        region,
                        observaciones,
                        esta_seleccionado,
                        fecha_creacion
                    FROM contextos_agricolas
                    WHERE agricultor_id = :agricultor_id
                      AND esta_seleccionado = 1
                    ORDER BY id DESC
                    LIMIT 1
                """),
                {"agricultor_id": id_a_entero(agricultor_id)},
            ).mappings().first()

            if not registro:
                return None

            return self._contexto_a_entidad(dict(registro))

    def guardar_consulta(self, consulta: Consulta) -> None:
        with self._session_factory() as session:
            resultado = session.execute(
                text("""
                    INSERT INTO consultas (
                        agricultor_id,
                        contexto_id,
                        pregunta,
                        fecha_creacion
                    )
                    VALUES (
                        :agricultor_id,
                        :contexto_id,
                        :pregunta,
                        :fecha_creacion
                    )
                """),
                {
                    "agricultor_id": id_a_entero(consulta.agricultor_id),
                    "contexto_id": id_a_entero(consulta.contexto_id),
                    "pregunta": consulta.texto.value,
                    "fecha_creacion": consulta.creado_en,
                },
            )

            consulta.id = id_a_dominio(resultado.lastrowid)
            session.commit()

    def guardar_respuesta(self, respuesta: Respuesta) -> None:
        with self._session_factory() as session:
            resultado = session.execute(
                text("""
                    INSERT INTO respuestas (
                        consulta_id,
                        respuesta,
                        metodo_generacion,
                        fecha_creacion
                    )
                    VALUES (
                        :consulta_id,
                        :respuesta,
                        :metodo_generacion,
                        :fecha_creacion
                    )
                """),
                {
                    "consulta_id": id_a_entero(respuesta.consulta_id),
                    "respuesta": respuesta.texto_respuesta,
                    "metodo_generacion": (
                        (respuesta.metodo_generacion or "")[:50] or None
                    ),
                    "fecha_creacion": respuesta.creado_en,
                },
            )

            respuesta.id = id_a_dominio(resultado.lastrowid)
            session.commit()

    def _contexto_a_entidad(
        self, registro: dict[str, object]
    ) -> ContextoAgricola:
        nombre = (str(registro["nombre_parcela"] or "")).strip() or None
        observaciones = (str(registro["observaciones"] or "")).strip() or None

        return ContextoAgricola(
            contexto_id=id_a_dominio(registro["id"]),
            agricultor_id=id_a_dominio(registro["agricultor_id"]),
            nombre_predio=nombre,
            cultivo=Cultivo(str(registro["cultivo"])),
            region=Region(str(registro["region"])),
            observaciones=observaciones,
            esta_seleccionado=bool(registro["esta_seleccionado"]),
            creado_en=registro["fecha_creacion"],
        )
