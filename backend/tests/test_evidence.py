from uuid import uuid4

import pytest

from app.domain.entities.evidencia import Evidencia
from app.domain.exceptions import ErrorEvidenciaInvalida
from app.domain.ports.output.repositorio_evidencia_port import PuertoRepositorioEvidencia
from app.domain.ports.output.text_generation_port import PasajeRecuperado
from app.infrastructure.adapters.output.generation.adaptador_generacion_plantilla import (
    AdaptadorGeneracionPlantilla,
)


class RepositorioEvidenciaEnMemoria(PuertoRepositorioEvidencia):
    def __init__(self) -> None:
        self.evidencias: list[Evidencia] = []

    def guardar_todas(self, evidencias: list[Evidencia]) -> None:
        self.evidencias.extend(evidencias)

    def listar_por_consulta_id(self, consulta_id: str) -> list[Evidencia]:
        return [item for item in self.evidencias if item.consulta_id == consulta_id]


def test_evidence_identifies_document_content_and_relevance() -> None:
    evidence = Evidencia.crear(
        consulta_id=str(uuid4()),
        respuesta_id=str(uuid4()),
        documento_id=str(uuid4()),
        fragmento_id=f"{'a' * 64}:chunk:0000",
        extracto="Riego frecuente en floración.",
        puntaje_similitud=0.76,
        orden_relevancia=1,
        titulo_documento="Riego de papa",
    )
    assert evidence.documento_id
    assert evidence.extracto == "Riego frecuente en floración."
    assert evidence.puntaje_similitud == 0.76
    assert evidence.titulo_documento == "Riego de papa"


def test_evidence_rejects_empty_excerpt() -> None:
    with pytest.raises(ErrorEvidenciaInvalida, match="contenido recuperado"):
        Evidencia.crear(
            consulta_id=str(uuid4()),
            respuesta_id=str(uuid4()),
            documento_id=str(uuid4()),
            fragmento_id="hash:chunk:0000",
            extracto="  ",
            puntaje_similitud=0.5,
            orden_relevancia=1,
        )


def test_evidence_repository_persists_association_to_query() -> None:
    repository = RepositorioEvidenciaEnMemoria()
    query_id = str(uuid4())
    evidence = Evidencia.crear(
        consulta_id=query_id,
        respuesta_id=str(uuid4()),
        documento_id=str(uuid4()),
        fragmento_id="hash:chunk:0000",
        extracto="Cubrir plantones jóvenes.",
        puntaje_similitud=0.64,
        orden_relevancia=1,
    )
    repository.guardar_todas([evidence])
    stored = repository.listar_por_consulta_id(query_id)
    assert len(stored) == 1
    assert stored[0].consulta_id == query_id
    assert stored[0].extracto == "Cubrir plantones jóvenes."
    assert repository.listar_por_consulta_id("missing") == []


def test_template_generation_uses_evidences() -> None:
    adapter = AdaptadorGeneracionPlantilla()
    generated = adapter.generar(
        texto_consulta="¿Cómo riego la papa?",
        cultivo="papa",
        region="Huancayo",
        pasajes=[
            PasajeRecuperado(
                titulo="Riego de papa",
                extracto="La papa en sierra requiere riegos frecuentes en floración.",
            )
        ],
    )
    assert generated.metodo_generacion == "template"
    assert "papa" in generated.texto_respuesta
    assert "Huancayo" in generated.texto_respuesta
    assert "base de conocimiento" in generated.texto_respuesta.lower()
    assert "floración" in generated.texto_respuesta
    assert "modelo de IA externo" in generated.texto_respuesta


def test_template_generation_without_evidences_is_controlled() -> None:
    adapter = AdaptadorGeneracionPlantilla()
    generated = adapter.generar(
        texto_consulta="¿Qué hago?",
        cultivo="papa",
        region="Huancayo",
        pasajes=[],
    )
    assert generated.metodo_generacion == "template"
    assert "No se encontró información suficiente" in generated.texto_respuesta
    assert "papa" in generated.texto_respuesta
    assert "Huancayo" in generated.texto_respuesta
    assert adapter.MARCA_SIN_RESULTADOS in generated.texto_respuesta
