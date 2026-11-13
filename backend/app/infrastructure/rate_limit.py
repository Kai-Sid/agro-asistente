"""Limitador en memoria por clave (IP / email). Sin dependencia externa."""

from __future__ import annotations

import threading
import time
from collections import defaultdict


class LimitadorVentana:
    def __init__(self) -> None:
        self._eventos: dict[str, list[float]] = defaultdict(list)
        self._candado = threading.Lock()

    def permitir(self, clave: str, maximo: int, ventana_segundos: int) -> bool:
        if maximo <= 0 or ventana_segundos <= 0:
            return True
        ahora = time.monotonic()
        inicio = ahora - ventana_segundos
        with self._candado:
            cola = self._eventos[clave]
            self._eventos[clave] = [t for t in cola if t >= inicio]
            if len(self._eventos[clave]) >= maximo:
                return False
            self._eventos[clave].append(ahora)
            return True

    def reiniciar(self) -> None:
        with self._candado:
            self._eventos.clear()


limitador_global = LimitadorVentana()
