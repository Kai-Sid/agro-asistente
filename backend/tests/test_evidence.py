from uuid import uuid4

from app.domain.entities.evidence import Evidence
from app.domain.exceptions import InvalidEvidenceError
from app.domain.ports.output.evidence_repository_port import EvidenceRepositoryPort
from app.infrastructure.adapters.output.generation.template_generation_adapter import (
    TemplateGenerationAdapter,
)
from app.domain.ports.output.text_generation_port import RetrievedPassage
import pytest


class InMemoryEvidenceRepository(EvidenceRepositoryPort):
    def __init__(self) -> None:
        self.evidences: list[Evidence] = []

    def save_all(self, evidences: list[Evidence]) -> None:
        self.evidences.extend(evidences)

    def list_by_query_id(self, query_id: str) -> list[Evidence]:
        return [item for item in self.evidences if item.query_id == query_id]


def test_evidence_identifies_document_content_and_relevance() -> None:
    evidence = Evidence.create(
        query_id=str(uuid4()),
        response_id=str(uuid4()),
        document_id=str(uuid4()),
        chunk_id=f"{'a' * 64}:chunk:0000",
        excerpt="Riego frecuente en floración.",
        similarity_score=0.76,
        rank_order=1,
        document_title="Riego de papa",
    )
    assert evidence.document_id
    assert evidence.excerpt == "Riego frecuente en floración."
    assert evidence.similarity_score == 0.76
    assert evidence.document_title == "Riego de papa"


def test_evidence_rejects_empty_excerpt() -> None:
    with pytest.raises(InvalidEvidenceError, match="contenido recuperado"):
        Evidence.create(
            query_id=str(uuid4()),
            response_id=str(uuid4()),
            document_id=str(uuid4()),
            chunk_id="hash:chunk:0000",
            excerpt="  ",
            similarity_score=0.5,
            rank_order=1,
        )


def test_evidence_repository_persists_association_to_query() -> None:
    repository = InMemoryEvidenceRepository()
    query_id = str(uuid4())
    evidence = Evidence.create(
        query_id=query_id,
        response_id=str(uuid4()),
        document_id=str(uuid4()),
        chunk_id="hash:chunk:0000",
        excerpt="Cubrir plantones jóvenes.",
        similarity_score=0.64,
        rank_order=1,
    )
    repository.save_all([evidence])
    stored = repository.list_by_query_id(query_id)
    assert len(stored) == 1
    assert stored[0].query_id == query_id
    assert stored[0].excerpt == "Cubrir plantones jóvenes."
    assert repository.list_by_query_id("missing") == []


def test_template_generation_uses_evidences() -> None:
    adapter = TemplateGenerationAdapter()
    generated = adapter.generate(
        query_text="¿Cómo riego la papa?",
        crop="papa",
        region="Huancayo",
        passages=[
            RetrievedPassage(
                title="Riego de papa",
                excerpt="La papa en sierra requiere riegos frecuentes en floración.",
            )
        ],
    )
    assert generated.generation_method == "template"
    assert "papa" in generated.answer_text
    assert "Huancayo" in generated.answer_text
    assert "base de conocimiento" in generated.answer_text.lower()
    assert "floración" in generated.answer_text
    assert "modelo de IA externo" in generated.answer_text


def test_template_generation_without_evidences_is_controlled() -> None:
    adapter = TemplateGenerationAdapter()
    generated = adapter.generate(
        query_text="¿Qué hago?",
        crop="papa",
        region="Huancayo",
        passages=[],
    )
    assert generated.generation_method == "template"
    assert "No se encontró información suficiente" in generated.answer_text
    assert "papa" in generated.answer_text
    assert "Huancayo" in generated.answer_text
    assert adapter.NO_RESULTS_MARK in generated.answer_text
