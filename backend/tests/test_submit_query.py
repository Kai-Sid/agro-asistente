from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest

from app.application.services.rag_retrieval_service import RetrievedSnippet
from app.application.useCases.submit_query import SubmitQuery
from app.domain.entities.agricultural_context import AgriculturalContext
from app.domain.entities.evidence import Evidence
from app.domain.entities.query import Query
from app.domain.entities.response import Response
from app.domain.exceptions import InvalidQueryTextError, SelectedContextNotFoundError
from app.domain.ports.input.submit_query_port import SubmitQueryCommand
from app.domain.ports.output.evidence_repository_port import EvidenceRepositoryPort
from app.domain.ports.output.query_repository_port import QueryRepositoryPort
from app.domain.ports.output.text_generation_port import (
    GeneratedAnswer,
    RetrievedPassage,
    TextGenerationPort,
)
from app.domain.valueObjects.crop import Crop
from app.domain.valueObjects.query_text import QueryText
from app.domain.valueObjects.region import Region

FARMER_A = "farmer-a"
FARMER_B = "farmer-b"
QUESTION = "¿Qué puedo hacer para mejorar el cultivo de papa?"


class InMemoryQueryRepository(QueryRepositoryPort):
    def __init__(self) -> None:
        self.selected_contexts: dict[str, AgriculturalContext] = {}
        self.queries: list[Query] = []
        self.responses: list[Response] = []

    def find_selected_context(self, farmer_id: str) -> AgriculturalContext | None:
        context = self.selected_contexts.get(farmer_id)
        if context is None or context.farmer_id != farmer_id:
            return None
        return context

    def save_query(self, query: Query) -> None:
        self.queries.append(query)

    def save_response(self, response: Response) -> None:
        self.responses.append(response)


class InMemoryEvidenceRepository(EvidenceRepositoryPort):
    def __init__(self) -> None:
        self.evidences: list[Evidence] = []

    def save_all(self, evidences: list[Evidence]) -> None:
        self.evidences.extend(evidences)

    def list_by_query_id(self, query_id: str) -> list[Evidence]:
        return [item for item in self.evidences if item.query_id == query_id]


class FakeTextGeneration(TextGenerationPort):
    def generate(
        self,
        query_text: str,
        crop: str,
        region: str,
        passages: list[RetrievedPassage] | None = None,
    ) -> GeneratedAnswer:
        extra = ""
        if passages:
            extra = "|" + "|".join(item.excerpt for item in passages)
        return GeneratedAnswer(
            answer_text=f"FAKE:{crop}:{region}:{query_text}{extra}",
            generation_method="template",
        )


class FakeRagRetrieval:
    def __init__(self, snippets: list[RetrievedSnippet] | None = None) -> None:
        self.snippets = snippets or []
        self.queries: list[str] = []

    def retrieve(self, query_text: str) -> list[RetrievedSnippet]:
        self.queries.append(query_text)
        return list(self.snippets)


def _context(
    farmer_id: str,
    crop: str = "papa",
    region: str = "Huancayo",
    plot_name: str | None = "Parcela 1",
) -> AgriculturalContext:
    return AgriculturalContext(
        context_id=str(uuid4()),
        farmer_id=farmer_id,
        plot_name=plot_name,
        crop=Crop(crop),
        region=Region(region),
        notes=None,
        is_selected=True,
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )


def _use_case(
    repository: InMemoryQueryRepository | None = None,
    generation: TextGenerationPort | None = None,
    rag: FakeRagRetrieval | None = None,
    evidence_repository: InMemoryEvidenceRepository | None = None,
) -> tuple[SubmitQuery, InMemoryQueryRepository, TextGenerationPort, FakeRagRetrieval, InMemoryEvidenceRepository]:
    repo = repository or InMemoryQueryRepository()
    generator = generation or FakeTextGeneration()
    retrieval = rag or FakeRagRetrieval()
    evidences = evidence_repository or InMemoryEvidenceRepository()
    return SubmitQuery(repo, generator, retrieval, evidences), repo, generator, retrieval, evidences


def test_submit_query_success() -> None:
    use_case, repository, _generation, _rag, _evidences = _use_case()
    context = _context(FARMER_A)
    repository.selected_contexts[FARMER_A] = context

    result = use_case.execute(SubmitQueryCommand(farmer_id=FARMER_A, text=QUESTION))

    assert result.text == QUESTION
    assert result.context.id == context.id
    assert result.context.crop == "papa"
    assert result.context.region == "Huancayo"
    assert result.generation_method == "template"
    assert result.id
    assert result.created_at


def test_submit_query_empty_text() -> None:
    use_case, repository, _generation, _rag, _evidences = _use_case()
    repository.selected_contexts[FARMER_A] = _context(FARMER_A)
    with pytest.raises(InvalidQueryTextError, match="obligatorio"):
        use_case.execute(SubmitQueryCommand(farmer_id=FARMER_A, text="   "))


def test_submit_query_invalid_text_too_long() -> None:
    use_case, repository, _generation, _rag, _evidences = _use_case()
    repository.selected_contexts[FARMER_A] = _context(FARMER_A)
    with pytest.raises(InvalidQueryTextError, match="longitud"):
        use_case.execute(
            SubmitQueryCommand(farmer_id=FARMER_A, text="a" * (QueryText.MAX_LENGTH + 1))
        )


def test_submit_query_without_selected_context() -> None:
    use_case, _repository, _generation, _rag, _evidences = _use_case()
    with pytest.raises(SelectedContextNotFoundError, match="contexto agrícola"):
        use_case.execute(SubmitQueryCommand(farmer_id=FARMER_A, text=QUESTION))


def test_submit_query_uses_authenticated_farmer_selected_context() -> None:
    use_case, repository, _generation, _rag, _evidences = _use_case()
    context_a = _context(FARMER_A, crop="papa", region="Huancayo")
    context_b = _context(FARMER_B, crop="maiz", region="Cusco")
    repository.selected_contexts[FARMER_A] = context_a
    repository.selected_contexts[FARMER_B] = context_b

    result = use_case.execute(SubmitQueryCommand(farmer_id=FARMER_A, text=QUESTION))

    assert result.context.id == context_a.id
    assert result.context.crop == "papa"
    assert result.context.region == "Huancayo"
    assert result.context.id != context_b.id
    assert repository.queries[0].farmer_id == FARMER_A
    assert repository.queries[0].context_id == context_a.id


def test_submit_query_persists_query() -> None:
    use_case, repository, _generation, _rag, _evidences = _use_case()
    context = _context(FARMER_A)
    repository.selected_contexts[FARMER_A] = context

    result = use_case.execute(SubmitQueryCommand(farmer_id=FARMER_A, text=QUESTION))

    assert len(repository.queries) == 1
    stored = repository.queries[0]
    assert stored.id == result.id
    assert stored.farmer_id == FARMER_A
    assert stored.context_id == context.id
    assert stored.text.value == QUESTION
    assert stored.created_at is not None


def test_submit_query_uses_text_generation_port() -> None:
    use_case, repository, _generation, _rag, _evidences = _use_case()
    repository.selected_contexts[FARMER_A] = _context(FARMER_A, crop="papa", region="Huancayo")

    result = use_case.execute(SubmitQueryCommand(farmer_id=FARMER_A, text=QUESTION))

    assert result.answer == f"FAKE:papa:Huancayo:{QUESTION}"
    assert result.generation_method == "template"


def test_submit_query_persists_response() -> None:
    use_case, repository, _generation, _rag, _evidences = _use_case()
    repository.selected_contexts[FARMER_A] = _context(FARMER_A)

    result = use_case.execute(SubmitQueryCommand(farmer_id=FARMER_A, text=QUESTION))

    assert len(repository.responses) == 1
    stored = repository.responses[0]
    assert stored.query_id == result.id
    assert stored.answer_text == result.answer
    assert stored.generation_method == "template"


def test_submit_query_use_case_does_not_import_frameworks_or_sdks() -> None:
    source = (
        Path(__file__).resolve().parents[1]
        / "app"
        / "application"
        / "useCases"
        / "submit_query.py"
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    forbidden = (
        "fastapi",
        "sqlalchemy",
        "chromadb",
        "chroma",
        "openai",
        "anthropic",
        "langchain",
        "httpx",
        "pydantic",
        "import jwt",
        "from jwt",
        "import bcrypt",
        "pymysql",
    )
    for item in forbidden:
        assert item not in lowered
    assert "queryrepositoryport" in lowered
    assert "textgenerationport" in lowered
    assert "evidencerepositoryport" in lowered
    assert "mysqlqueryrepository" not in lowered
    assert "templategenerationadapter" not in lowered
    assert "chromavectorstoreadapter" not in lowered


def test_submit_query_associates_and_persists_evidences() -> None:
    snippet = RetrievedSnippet(
        document_id="doc-1",
        document_title="Riego de papa",
        chunk_id="abc:chunk:0000",
        excerpt="Riego frecuente en floración.",
        similarity_score=0.81,
    )
    use_case, repository, _generation, rag, evidence_repo = _use_case(
        rag=FakeRagRetrieval([snippet])
    )
    repository.selected_contexts[FARMER_A] = _context(FARMER_A)

    result = use_case.execute(SubmitQueryCommand(farmer_id=FARMER_A, text=QUESTION))

    assert rag.queries == [QUESTION]
    assert len(result.evidences) == 1
    assert result.evidences[0].document_id == "doc-1"
    assert result.evidences[0].excerpt == "Riego frecuente en floración."
    assert result.evidences[0].rank_order == 1
    assert len(evidence_repo.evidences) == 1
    stored = evidence_repo.evidences[0]
    assert stored.query_id == result.id
    assert stored.response_id == repository.responses[0].id
    assert stored.document_id == "doc-1"
    assert "Riego frecuente" in result.answer


def test_submit_query_without_relevant_results_does_not_invent_evidence() -> None:
    use_case, repository, _generation, _rag, evidence_repo = _use_case()
    repository.selected_contexts[FARMER_A] = _context(FARMER_A)

    result = use_case.execute(SubmitQueryCommand(farmer_id=FARMER_A, text=QUESTION))

    assert result.evidences == ()
    assert evidence_repo.evidences == []
    assert result.answer == f"FAKE:papa:Huancayo:{QUESTION}"
