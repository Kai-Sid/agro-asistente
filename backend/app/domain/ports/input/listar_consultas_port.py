from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ResultadoHistorialConsulta:
    id: str
    text: str
    answer: str
    generation_method: str
    created_at: str


class PuertoListarConsultas(ABC):
    @abstractmethod
    def ejecutar(
        self, agricultor_id: str, limite: int = 20
    ) -> list[ResultadoHistorialConsulta]:
        """Lista consultas del agricultor autenticado (más recientes primero)."""
