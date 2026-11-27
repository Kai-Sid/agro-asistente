from sqlalchemy import Boolean, DateTime, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, sessionmaker

from app.domain.entities.contexto_agricola import ContextoAgricola
from app.domain.ports.output.repositorio_contexto_agricola_port import (
    PuertoRepositorioContextoAgricola,
)
from app.domain.valueObjects.cultivo import Cultivo
from app.domain.valueObjects.region import Region
from app.infrastructure.adapters.output.mysql.connection import (
    Base,
    id_a_dominio,
    id_a_entero,
)


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
        self._session_factory = session_factory

    def guardar(self, contexto: ContextoAgricola) -> None:
        with self._session_factory() as session:
            resultado = session.execute(
                text("""
                    INSERT INTO contextos_agricolas (
                        agricultor_id,
                        nombre_parcela,
                        cultivo,
                        region,
                        observaciones,
                        esta_seleccionado,
                        fecha_creacion
                    )
                    VALUES (
                        :agricultor_id,
                        :nombre_parcela,
                        :cultivo,
                        :region,
                        :observaciones,
                        :esta_seleccionado,
                        :fecha_creacion
                    )
                """),
                {
                    "agricultor_id": id_a_entero(contexto.agricultor_id),
                    "nombre_parcela": (contexto.nombre_predio or "")[:150],
                    "cultivo": contexto.cultivo.value[:100],
                    "region": contexto.region.value[:100],
                    "observaciones": contexto.observaciones,
                    "esta_seleccionado": bool(contexto.esta_seleccionado),
                    "fecha_creacion": contexto.creado_en,
                },
            )

            contexto.id = id_a_dominio(resultado.lastrowid)
            session.commit()

    def listar_por_agricultor(self, agricultor_id: str) -> list[ContextoAgricola]:
        with self._session_factory() as session:
            registros = session.execute(
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
                    ORDER BY fecha_creacion DESC, id DESC
                """),
                {"agricultor_id": id_a_entero(agricultor_id)},
            ).mappings().all()

            return [self._a_entidad(dict(registro)) for registro in registros]

    def buscar_por_id_para_agricultor(
        self, contexto_id: str, agricultor_id: str
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
                    WHERE id = :contexto_id
                      AND agricultor_id = :agricultor_id
                    LIMIT 1
                """),
                {
                    "contexto_id": id_a_entero(contexto_id),
                    "agricultor_id": id_a_entero(agricultor_id),
                },
            ).mappings().first()

            return self._a_entidad(dict(registro)) if registro else None

    def seleccionar_para_agricultor(
        self, contexto_id: str, agricultor_id: str
    ) -> ContextoAgricola | None:
        with self._session_factory() as session:
            parametros = {
                "contexto_id": id_a_entero(contexto_id),
                "agricultor_id": id_a_entero(agricultor_id),
            }

            existe = session.execute(
                text("""
                    SELECT 1
                    FROM contextos_agricolas
                    WHERE id = :contexto_id
                      AND agricultor_id = :agricultor_id
                    LIMIT 1
                """),
                parametros,
            ).first()

            if existe:
                session.execute(
                    text("""
                        UPDATE contextos_agricolas
                        SET esta_seleccionado = CASE
                            WHEN id = :contexto_id THEN 1
                            ELSE 0
                        END
                        WHERE agricultor_id = :agricultor_id
                    """),
                    parametros,
                )

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
                    WHERE id = :contexto_id
                      AND agricultor_id = :agricultor_id
                    LIMIT 1
                """),
                parametros,
            ).mappings().first()

            session.commit()

            return self._a_entidad(dict(registro)) if registro else None

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
