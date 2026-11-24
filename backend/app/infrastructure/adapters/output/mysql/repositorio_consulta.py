from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, sessionmaker

from app.domain.entities.consulta import Consulta
from app.domain.entities.contexto_agricola import ContextoAgricola
from app.domain.entities.respuesta import Respuesta
from app.domain.ports.output.repositorio_consulta_port import PuertoRepositorioConsulta
from app.domain.valueObjects.cultivo import Cultivo
from app.domain.valueObjects.region import Region
from app.infrastructure.adapters.output.mysql.connection import Base, id_a_dominio, id_a_entero
from app.infrastructure.adapters.output.mysql.procedures import MysqlStoredProcedureGateway


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
        self._procedures = MysqlStoredProcedureGateway(session_factory)

    def buscar_contexto_seleccionado(self, agricultor_id: str) -> ContextoAgricola | None:
        rows = self._procedures.call(
            "sp_contexto_agricola_buscar_seleccionado",
            (id_a_entero(agricultor_id),),
        )
        if not rows:
            return None
        registro = rows[0]
        nombre = str(registro["nombre_parcela"] or "").strip() or None
        observaciones = str(registro["observaciones"] or "").strip() or None
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

    def guardar_consulta(self, consulta: Consulta) -> None:
        rows = self._procedures.call(
            "sp_consulta_guardar",
            (
                id_a_entero(consulta.agricultor_id),
                id_a_entero(consulta.contexto_id),
                consulta.texto.value,
                consulta.creado_en,
            ),
        )
        if not rows:
            raise RuntimeError("El procedimiento no devolvió la consulta creada")
        consulta.id = id_a_dominio(rows[0]["id"])

    def guardar_respuesta(self, respuesta: Respuesta) -> None:
        rows = self._procedures.call(
            "sp_respuesta_guardar",
            (
                id_a_entero(respuesta.consulta_id),
                respuesta.texto_respuesta,
                (respuesta.metodo_generacion or "")[:50] or None,
                respuesta.creado_en,
            ),
        )
        if not rows:
            raise RuntimeError("El procedimiento no devolvió la respuesta creada")
        respuesta.id = id_a_dominio(rows[0]["id"])
