from sqlalchemy import Boolean, DateTime, String, select, update
from sqlalchemy.orm import Mapped, mapped_column, sessionmaker

from app.domain.entities.contexto_agricola import ContextoAgricola
from app.domain.ports.output.repositorio_contexto_agricola_port import (
    PuertoRepositorioContextoAgricola,
)
from app.domain.valueObjects.cultivo import Cultivo
from app.domain.valueObjects.region import Region
from app.infrastructure.adapters.output.mysql.connection import Base


class RegistroContextoAgricola(Base):
    __tablename__ = "agricultural_contexts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    farmer_id: Mapped[str] = mapped_column(String(36), nullable=False)
    plot_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    crop: Mapped[str] = mapped_column(String(50), nullable=False)
    region: Mapped[str] = mapped_column(String(120), nullable=False)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_selected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[object] = mapped_column(DateTime, nullable=False)


class RepositorioContextoAgricolaMysql(PuertoRepositorioContextoAgricola):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    def guardar(self, contexto: ContextoAgricola) -> None:
        registro = RegistroContextoAgricola(
            id=contexto.id,
            farmer_id=contexto.agricultor_id,
            plot_name=contexto.nombre_predio,
            crop=contexto.cultivo.value,
            region=contexto.region.value,
            notes=contexto.observaciones,
            is_selected=contexto.esta_seleccionado,
            created_at=contexto.creado_en,
        )
        with self._session_factory() as session:
            session.add(registro)
            session.commit()

    def listar_por_agricultor(self, agricultor_id: str) -> list[ContextoAgricola]:
        with self._session_factory() as session:
            registros = session.scalars(
                select(RegistroContextoAgricola)
                .where(RegistroContextoAgricola.farmer_id == agricultor_id)
                .order_by(RegistroContextoAgricola.created_at.desc())
            ).all()
            return [self._a_entidad(registro) for registro in registros]

    def buscar_por_id_para_agricultor(
        self, contexto_id: str, agricultor_id: str
    ) -> ContextoAgricola | None:
        with self._session_factory() as session:
            registro = session.scalar(
                select(RegistroContextoAgricola).where(
                    RegistroContextoAgricola.id == contexto_id,
                    RegistroContextoAgricola.farmer_id == agricultor_id,
                )
            )
            if registro is None:
                return None
            return self._a_entidad(registro)

    def seleccionar_para_agricultor(
        self, contexto_id: str, agricultor_id: str
    ) -> ContextoAgricola | None:
        with self._session_factory() as session:
            registro = session.scalar(
                select(RegistroContextoAgricola).where(
                    RegistroContextoAgricola.id == contexto_id,
                    RegistroContextoAgricola.farmer_id == agricultor_id,
                )
            )
            if registro is None:
                return None
            session.execute(
                update(RegistroContextoAgricola)
                .where(RegistroContextoAgricola.farmer_id == agricultor_id)
                .values(is_selected=False)
            )
            registro.is_selected = True
            session.commit()
            session.refresh(registro)
            return self._a_entidad(registro)

    def _a_entidad(self, registro: RegistroContextoAgricola) -> ContextoAgricola:
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
