from getpass import getpass

from app.infrastructure.adapters.output.mysql.connection import create_session_factory
from app.infrastructure.adapters.output.mysql.procedures import MysqlStoredProcedureGateway
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
    gateway = MysqlStoredProcedureGateway(create_session_factory(get_settings()))
    try:
        rows = gateway.call(
            "sp_administrador_crear",
            (nombre[:120], correo[:150], hash_contrasena),
        )
    except Exception as error:
        print(f"No se pudo crear el administrador: {error}")
        return 1

    if not rows:
        print("El procedimiento no devolvió el administrador creado.")
        return 1
    print(f"Administrador creado: {rows[0]['correo']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
