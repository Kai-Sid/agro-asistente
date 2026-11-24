from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, sessionmaker

from app.domain.entities.contexto_agricola import ContextoAgricola
from app.domain.ports.output.repositorio_contexto_agricola_port import (
    PuertoRepositorioContextoAgricola,
)
from app.domain.valueObjects.cultivo import Cultivo
from app.domain.valueObjects.region import Region
from app.infrastructure.adapters.output.mysql.connection import Base, id_a_dominio, id_a_entero
from app.infrastructure.adapters.output.mysql.procedures import MysqlStoredProcedureGateway


class RegistroContextoAgricola(Base):
    __tablename__ = "contextos_agricolas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agricultor_id: Mapped[int] = mapped_column(Integer, nullable=False)
    nombre_parcela: Mapped[str] = mapped_column(String(150), nullable=False)
    cultivo: Mapped[str] = mapped_column(String(100), nullable=False)
    region: Mapped[str] = mapped_column(String(100), nullable=False)
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    esta_seleccionado: Mapped[bool] = mapped_column(Boolean, nullable=True, default=False)
    fecha_creacion: Mapped[object] = mapped_column(DateTime, nullable=True)


class RepositorioContextoAgricolaMysql(PuertoRepositorioContextoAgricola):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._procedures = MysqlStoredProcedureGateway(session_factory)

    def guardar(self, contexto: ContextoAgricola) -> None:
        rows = self._procedures.call(
            "sp_contexto_agricola_guardar",
            (
                id_a_entero(contexto.agricultor_id),
                (contexto.nombre_predio or "")[:150],
                contexto.cultivo.value[:100],
                contexto.region.value[:100],
                contexto.observaciones,
                bool(contexto.esta_seleccionado),
                contexto.creado_en,
            ),
        )
        if not rows:
            raise RuntimeError("El procedimiento no devolvió el contexto creado")
        contexto.id = id_a_dominio(rows[0]["id"])

    def listar_por_agricultor(self, agricultor_id: str) -> list[ContextoAgricola]:
        rows = self._procedures.call(
            "sp_contextos_agricolas_listar_por_agricultor",
            (id_a_entero(agricultor_id),),
        )
        return [self._a_entidad(row) for row in rows]

    def buscar_por_id_para_agricultor(
        self, contexto_id: str, agricultor_id: str
    ) -> ContextoAgricola | None:
        rows = self._procedures.call(
            "sp_contexto_agricola_buscar_por_id_para_agricultor",
            (id_a_entero(contexto_id), id_a_entero(agricultor_id)),
        )
        return self._a_entidad(rows[0]) if rows else None

    def seleccionar_para_agricultor(
        self, contexto_id: str, agricultor_id: str
    ) -> ContextoAgricola | None:
        rows = self._procedures.call(
            "sp_contexto_agricola_seleccionar_para_agricultor",
            (id_a_entero(contexto_id), id_a_entero(agricultor_id)),
        )
        return self._a_entidad(rows[0]) if rows else None

    def _a_entidad(self, registro: dict[str, object]) -> ContextoAgricola:
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
