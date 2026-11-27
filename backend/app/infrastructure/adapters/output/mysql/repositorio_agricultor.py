import pymysql.err

from sqlalchemy import DateTime, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, sessionmaker

from app.domain.entities.agricultor import Agricultor
from app.domain.exceptions import ErrorCorreoDuplicado
from app.domain.ports.output.repositorio_agricultor_port import PuertoRepositorioAgricultor
from app.domain.valueObjects.email import Email
from app.domain.valueObjects.hash_contrasena import HashContrasena
from app.infrastructure.adapters.output.mysql.connection import Base, id_a_dominio


class RegistroAgricultor(Base):
    __tablename__ = "agricultores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre_completo: Mapped[str] = mapped_column(String(150), nullable=False)
    correo: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    contrasena_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    fecha_creacion: Mapped[object] = mapped_column(DateTime, nullable=True)


class RepositorioAgricultorMysql(PuertoRepositorioAgricultor):
    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    def existe_por_correo(self, email: Email) -> bool:
        with self._session_factory() as session:
            resultado = session.execute(
                text("""
                    SELECT EXISTS(
                        SELECT 1
                        FROM agricultores
                        WHERE correo = :correo
                    ) AS existe
                """),
                {"correo": email.value},
            ).scalar_one()

            return bool(resultado)

    def buscar_por_correo(self, email: Email) -> Agricultor | None:
        with self._session_factory() as session:
            registro = session.execute(
                text("""
                    SELECT
                        id,
                        nombre_completo,
                        correo,
                        contrasena_hash,
                        fecha_creacion
                    FROM agricultores
                    WHERE correo = :correo
                    LIMIT 1
                """),
                {"correo": email.value},
            ).mappings().first()

            return self._a_entidad(dict(registro)) if registro else None

    def guardar(self, agricultor: Agricultor) -> None:
        try:
            with self._session_factory() as session:
                resultado = session.execute(
                    text("""
                        INSERT INTO agricultores (
                            nombre_completo,
                            correo,
                            contrasena_hash,
                            fecha_creacion
                        )
                        VALUES (
                            :nombre_completo,
                            :correo,
                            :contrasena_hash,
                            :fecha_creacion
                        )
                    """),
                    {
                        "nombre_completo": agricultor.nombre_completo[:150],
                        "correo": agricultor.email.value[:150],
                        "contrasena_hash": agricultor.hash_contrasena.value,
                        "fecha_creacion": agricultor.creado_en,
                    },
                )

                agricultor.id = id_a_dominio(resultado.lastrowid)
                session.commit()

        except pymysql.err.IntegrityError as error:
            if error.args and error.args[0] == 1062:
                raise ErrorCorreoDuplicado(
                    "El correo electrónico ya está registrado"
                ) from error
            raise

    def _a_entidad(self, registro: dict[str, object]) -> Agricultor:
        nombres, apellidos = _separar_nombre_completo(
            str(registro["nombre_completo"])
        )
        creado = registro["fecha_creacion"]

        return Agricultor(
            agricultor_id=id_a_dominio(registro["id"]),
            nombres=nombres,
            apellidos=apellidos,
            email=Email(str(registro["correo"])),
            hash_contrasena=HashContrasena(str(registro["contrasena_hash"])),
            creado_en=creado,
            actualizado_en=creado,
        )


def _separar_nombre_completo(nombre_completo: str) -> tuple[str, str]:
    partes = (nombre_completo or "").strip().split(" ", 1)

    if len(partes) == 1:
        return partes[0], ""

    return partes[0], partes[1]
