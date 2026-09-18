from sqlalchemy import DateTime, String, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Mapped, mapped_column, sessionmaker

from app.domain.entities.agricultor import Agricultor
from app.domain.exceptions import ErrorCorreoDuplicado
from app.domain.ports.output.repositorio_agricultor_port import PuertoRepositorioAgricultor
from app.domain.valueObjects.email import Email
from app.domain.valueObjects.hash_contrasena import HashContrasena
from app.infrastructure.adapters.output.mysql.connection import Base


class RegistroAgricultor(Base):
    __tablename__ = "farmers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(190), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[object] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[object] = mapped_column(DateTime, nullable=False)


class RepositorioAgricultorMysql(PuertoRepositorioAgricultor):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    def existe_por_correo(self, email: Email) -> bool:
        with self._session_factory() as session:
            agricultor_id = session.scalar(
                select(RegistroAgricultor.id).where(RegistroAgricultor.email == email.value)
            )
            return agricultor_id is not None

    def buscar_por_correo(self, email: Email) -> Agricultor | None:
        with self._session_factory() as session:
            registro = session.scalar(
                select(RegistroAgricultor).where(RegistroAgricultor.email == email.value)
            )
            if registro is None:
                return None
            return self._a_entidad(registro)

    def guardar(self, agricultor: Agricultor) -> None:
        registro = RegistroAgricultor(
            id=agricultor.id,
            full_name=agricultor.nombre_completo,
            email=agricultor.email.value,
            password_hash=agricultor.hash_contrasena.value,
            created_at=agricultor.creado_en,
            updated_at=agricultor.actualizado_en,
        )
        with self._session_factory() as session:
            session.add(registro)
            try:
                session.commit()
            except IntegrityError as error:
                session.rollback()
                raise ErrorCorreoDuplicado(
                    "El correo electrónico ya está registrado"
                ) from error

    def _a_entidad(self, registro: RegistroAgricultor) -> Agricultor:
        nombres, apellidos = _separar_nombre_completo(registro.full_name)
        return Agricultor(
            agricultor_id=registro.id,
            nombres=nombres,
            apellidos=apellidos,
            email=Email(registro.email),
            hash_contrasena=HashContrasena(registro.password_hash),
            creado_en=registro.created_at,
            actualizado_en=registro.updated_at,
        )


def _separar_nombre_completo(nombre_completo: str) -> tuple[str, str]:
    partes = (nombre_completo or "").strip().split(" ", 1)
    if len(partes) == 1:
        return partes[0], ""
    return partes[0], partes[1]
