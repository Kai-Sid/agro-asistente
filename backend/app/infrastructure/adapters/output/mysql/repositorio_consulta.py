from decimal import Decimal

from sqlalchemy import DateTime, Integer, String, Text, desc, select
from sqlalchemy.orm import Mapped, mapped_column, sessionmaker

from app.domain.entities.consulta import Consulta
from app.domain.entities.contexto_agricola import ContextoAgricola
from app.domain.entities.evidencia import Evidencia
from app.domain.entities.respuesta import Respuesta
from app.domain.ports.output.repositorio_consulta_port import PuertoRepositorioConsulta
from app.domain.valueObjects.cultivo import Cultivo
from app.domain.valueObjects.region import Region
from app.infrastructure.adapters.output.mysql.connection import (
    Base,
    id_a_dominio,
    id_a_entero,
)
from app.infrastructure.adapters.output.mysql.repositorio_contexto_agricola import (
    RegistroContextoAgricola,
)
from app.infrastructure.adapters.output.mysql.repositorio_evidencia import (
    RegistroEvidencia,
    _texto_con_fragmento,
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

    def buscar_contexto_seleccionado(self, agricultor_id: str) -> ContextoAgricola | None:
        with self._session_factory() as session:
            registro = session.scalar(
                select(RegistroContextoAgricola).where(
                    RegistroContextoAgricola.agricultor_id == id_a_entero(agricultor_id),
                    RegistroContextoAgricola.esta_seleccionado.is_(True),
                )
            )
            if registro is None:
                return None
            nombre = (registro.nombre_parcela or "").strip() or None
            observaciones = (registro.observaciones or "").strip() or None
            return ContextoAgricola(
                contexto_id=id_a_dominio(registro.id),
                agricultor_id=id_a_dominio(registro.agricultor_id),
                nombre_predio=nombre,
                cultivo=Cultivo(registro.cultivo),
                region=Region(registro.region),
                observaciones=observaciones,
                esta_seleccionado=bool(registro.esta_seleccionado),
                creado_en=registro.fecha_creacion,
            )

    def guardar_consulta(self, consulta: Consulta) -> None:
        registro = RegistroConsulta(
            agricultor_id=id_a_entero(consulta.agricultor_id),
            contexto_id=id_a_entero(consulta.contexto_id),
            pregunta=consulta.texto.value,
            fecha_creacion=consulta.creado_en,
        )
        with self._session_factory() as session:
            session.add(registro)
            session.flush()
            consulta.id = id_a_dominio(registro.id)
            session.commit()

    def guardar_respuesta(self, respuesta: Respuesta) -> None:
        registro = RegistroRespuesta(
            consulta_id=id_a_entero(respuesta.consulta_id),
            respuesta=respuesta.texto_respuesta,
            metodo_generacion=(respuesta.metodo_generacion or "")[:50] or None,
            fecha_creacion=respuesta.creado_en,
        )
        with self._session_factory() as session:
            session.add(registro)
            session.flush()
            respuesta.id = id_a_dominio(registro.id)
            session.commit()

    def guardar_interaccion(
        self,
        consulta: Consulta,
        respuesta: Respuesta,
        evidencias: list[Evidencia] | None = None,
    ) -> None:
        evidencias = evidencias or []
        with self._session_factory() as session:
            try:
                registro_consulta = RegistroConsulta(
                    agricultor_id=id_a_entero(consulta.agricultor_id),
                    contexto_id=id_a_entero(consulta.contexto_id),
                    pregunta=consulta.texto.value,
                    fecha_creacion=consulta.creado_en,
                )
                session.add(registro_consulta)
                session.flush()
                consulta.id = id_a_dominio(registro_consulta.id)
                respuesta.consulta_id = consulta.id

                registro_respuesta = RegistroRespuesta(
                    consulta_id=id_a_entero(respuesta.consulta_id),
                    respuesta=respuesta.texto_respuesta,
                    metodo_generacion=(respuesta.metodo_generacion or "")[:50] or None,
                    fecha_creacion=respuesta.creado_en,
                )
                session.add(registro_respuesta)
                session.flush()
                respuesta.id = id_a_dominio(registro_respuesta.id)

                for item in evidencias:
                    item.consulta_id = consulta.id
                    item.respuesta_id = respuesta.id
                    session.add(
                        RegistroEvidencia(
                            consulta_id=id_a_entero(item.consulta_id),
                            respuesta_id=id_a_entero(item.respuesta_id),
                            documento_id=id_a_entero(item.documento_id),
                            titulo_documento=(item.titulo_documento or "").strip(),
                            texto_fragmento=_texto_con_fragmento(
                                item.fragmento_id, item.extracto
                            ),
                            puntuacion_similitud=Decimal(str(item.puntaje_similitud)),
                        )
                    )
                session.commit()
            except Exception:
                session.rollback()
                raise

    def listar_por_agricultor(
        self, agricultor_id: str, limite: int = 20
    ) -> list[dict[str, str]]:
        tope = max(1, min(int(limite or 20), 50))
        with self._session_factory() as session:
            filas = session.execute(
                select(RegistroConsulta, RegistroRespuesta)
                .outerjoin(
                    RegistroRespuesta,
                    RegistroRespuesta.consulta_id == RegistroConsulta.id,
                )
                .where(RegistroConsulta.agricultor_id == id_a_entero(agricultor_id))
                .order_by(desc(RegistroConsulta.id))
                .limit(tope)
            ).all()
            historial: list[dict[str, str]] = []
            for consulta, respuesta in filas:
                creado = consulta.fecha_creacion
                creado_txt = (
                    creado.isoformat()
                    if creado is not None and hasattr(creado, "isoformat")
                    else str(creado or "")
                )
                historial.append(
                    {
                        "id": id_a_dominio(consulta.id),
                        "text": consulta.pregunta or "",
                        "answer": (respuesta.respuesta if respuesta else "") or "",
                        "generation_method": (
                            (respuesta.metodo_generacion if respuesta else "") or ""
                        ),
                        "created_at": creado_txt,
                    }
                )
            return historial
