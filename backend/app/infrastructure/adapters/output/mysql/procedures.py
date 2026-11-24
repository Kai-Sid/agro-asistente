from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from typing import Any

from sqlalchemy.orm import sessionmaker

ProcedureCall = tuple[str, Sequence[Any]]
_PROCEDURE_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


class MysqlStoredProcedureGateway:
    """Invoca únicamente procedimientos MySQL con el protocolo callproc de PyMySQL."""

    def __init__(self, session_factory: sessionmaker) -> None:
        self._session_factory = session_factory

    def call(self, name: str, parameters: Sequence[Any] = ()) -> list[dict[str, Any]]:
        return self.call_many([(name, parameters)])[0]

    def call_many(
        self, calls: Iterable[ProcedureCall]
    ) -> list[list[dict[str, Any]]]:
        results: list[list[dict[str, Any]]] = []
        with self._session_factory() as session:
            try:
                raw_connection = session.connection().connection.driver_connection
                with raw_connection.cursor() as cursor:
                    for name, parameters in calls:
                        self._validate_name(name)
                        cursor.callproc(name, tuple(parameters))
                        result_rows: list[dict[str, Any]] = []
                        while True:
                            if cursor.description is not None:
                                columns = [column[0] for column in cursor.description]
                                result_rows = [
                                    dict(zip(columns, row, strict=True))
                                    for row in cursor.fetchall()
                                ]
                            if not cursor.nextset():
                                break
                        results.append(result_rows)
                session.commit()
                return results
            except Exception:
                session.rollback()
                raise

    @staticmethod
    def _validate_name(name: str) -> None:
        if not _PROCEDURE_NAME.fullmatch(name):
            raise ValueError("Nombre de procedimiento almacenado inválido")
