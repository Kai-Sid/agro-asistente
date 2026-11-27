from getpass import getpass

from sqlalchemy import text

from app.infrastructure.adapters.output.mysql.connection import create_session_factory
from app.infrastructure.adapters.output.security.hasher_contrasena_bcrypt import (
    HasherContrasenaBcrypt,
)
from app.infrastructure.config.settings import get_settings


def main() -> int:
    nombre = input("Nombre del administrador: ").strip()
    correo = input("Correo del administrador: ").strip().lower()
    contrasena = getpass("Contraseña (mínimo 12 caracteres): ")
    confirmacion = getpass("Repite la contraseña: ")

    if not nombre or not correo or contrasena != confirmacion:
        print("Verifica nombre, correo y confirmación de contraseña.")
        return 1

    if len(contrasena) < 12:
        print("La contraseña debe tener al menos 12 caracteres.")
        return 1

    hasher = HasherContrasenaBcrypt()
    hash_contrasena = hasher.hashear_contrasena(contrasena)

    session_factory = create_session_factory(get_settings())

    try:
        with session_factory() as session:
            existente = session.execute(
                text("""
                    SELECT id
                    FROM administradores
                    WHERE correo = :correo
                    LIMIT 1
                """),
                {"correo": correo},
            ).first()

            if existente:
                print("Ya existe un administrador con ese correo.")
                return 1

            resultado = session.execute(
                text("""
                    INSERT INTO administradores (
                        nombre,
                        correo,
                        contrasena_hash,
                        activo
                    )
                    VALUES (
                        :nombre,
                        :correo,
                        :contrasena_hash,
                        1
                    )
                """),
                {
                    "nombre": nombre[:120],
                    "correo": correo[:150],
                    "contrasena_hash": hash_contrasena,
                },
            )

            administrador_id = resultado.lastrowid

            if not administrador_id:
                raise RuntimeError(
                    "No se pudo obtener el identificador del administrador."
                )

            session.commit()

        print(f"Administrador creado: {correo}")
        print(f"ID del administrador: {administrador_id}")
        return 0

    except Exception as error:
        print(f"No se pudo crear el administrador: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
