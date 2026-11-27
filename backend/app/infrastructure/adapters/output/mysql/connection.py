import pymysql.err
from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import URL
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.infrastructure.config.settings import Settings, get_settings


class Base(DeclarativeBase):
    """Declarative base conservada para compatibilidad de infraestructura MySQL."""


def create_mysql_engine(settings: Settings | None = None) -> Engine:
    current = settings or get_settings()

    connect_args = {
        "connect_timeout": 10,
    }

    ssl_ca = getattr(current, "mysql_ssl_ca", None)

    if ssl_ca:
        connect_args["ssl"] = {
            "ca": ssl_ca,
            "check_hostname": True,
        }

    return create_engine(
        current.mysql_url,
        pool_pre_ping=True,
        future=True,
        connect_args=connect_args,
    )


def create_session_factory(settings: Settings | None = None) -> sessionmaker:
    engine = create_mysql_engine(settings)
    return sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        future=True,
    )


def ping_mysql(settings: Settings | None = None) -> bool:
    """Comprueba la conexión con MySQL o TiDB Cloud."""
    engine = create_mysql_engine(settings)
    raw_connection = None

    try:
        raw_connection = engine.raw_connection()
        raw_connection.ping(reconnect=False)
        return True
    except (SQLAlchemyError, pymysql.err.Error, OSError):
        return False
    finally:
        if raw_connection is not None:
            raw_connection.close()
        engine.dispose()


def id_a_entero(valor: str | int) -> int:
    return int(str(valor).strip())


def id_a_dominio(valor: int | str) -> str:
    return str(valor)
