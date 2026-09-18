from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class GeneratedAnswer:
    answer_text: str
    generation_method: str


@dataclass(frozen=True)
class RetrievedPassage:
    """Pasaje recuperado para construir la respuesta inicial. No es un LLM."""

    title: str
    excerpt: str


class TextGenerationPort(ABC):
    """Puerto de salida para generar el texto de una respuesta agrícola.

    PMV1 usa una plantilla. El dominio no conoce el adaptador concreto.
    """

    @abstractmethod
    def generate(
        self,
        query_text: str,
        crop: str,
        region: str,
        passages: list[RetrievedPassage] | None = None,
    ) -> GeneratedAnswer:
        """Genera una respuesta a partir de la consulta, el contexto y pasajes recuperados."""
