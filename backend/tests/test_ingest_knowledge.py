from pathlib import Path

import pytest

from app.application.useCases.ingest_knowledge import IngestKnowledge
from app.domain.entities.knowledge_document import KnowledgeDocument
from app.domain.exceptions import DuplicateKnowledgeDocumentError, InvalidKnowledgeDocumentError
from app.domain.ports.input.ingest_knowledge_port import IngestKnowledgeCommand
from app.domain.ports.output.knowledge_document_repository_port import (
    KnowledgeDocumentRepositoryPort,
)
from app.domain.valueObjects.content_hash import ContentHash

CONTENT = """# Riego de papa (material de prueba)

Texto de prueba para HU-05. No es una guía oficial.
"""


class InMemoryKnowledgeRepository(KnowledgeDocumentRepositoryPort):
    def __init__(self) -> None:
        self.documents: list[KnowledgeDocument] = []
        self.contents: dict[str, str] = {}

    def exists_by_hash(self, content_hash: ContentHash) -> bool:
        return any(document.content_hash == content_hash for document in self.documents)

    def save(self, document: KnowledgeDocument, content: str) -> None:
        self.documents.append(document)
        self.contents[document.id] = content

    def list_all(self) -> list[KnowledgeDocument]:
        return list(self.documents)

    def find_by_id(self, document_id: str) -> KnowledgeDocument | None:
        for document in self.documents:
            if document.id == document_id:
                return document
        return None

    def read_content(self, document: KnowledgeDocument) -> str:
        return self.contents[document.id]

    def update_chunk_count(self, document_id: str, chunk_count: int) -> None:
        for document in self.documents:
            if document.id == document_id:
                document.chunk_count = chunk_count
                return


def _use_case() -> tuple[IngestKnowledge, InMemoryKnowledgeRepository]:
    repository = InMemoryKnowledgeRepository()
    return IngestKnowledge(repository), repository


def test_ingest_knowledge_success() -> None:
    use_case, repository = _use_case()
    result = use_case.execute(
        IngestKnowledgeCommand(title="Riego de papa", topic="papa", content=CONTENT)
    )
    assert result.status == "registered"
    assert result.title == "Riego de papa"
    assert result.topic == "papa"
    assert result.chunk_count == 0
    assert result.source_path.endswith(".md")
    assert len(result.content_hash) == 64
    assert len(repository.documents) == 1


def test_ingest_knowledge_empty_content() -> None:
    use_case, _repository = _use_case()
    with pytest.raises(InvalidKnowledgeDocumentError, match="contenido"):
        use_case.execute(
            IngestKnowledgeCommand(title="Riego", topic="papa", content="   ")
        )


def test_ingest_knowledge_invalid_content_too_long() -> None:
    use_case, _repository = _use_case()
    with pytest.raises(InvalidKnowledgeDocumentError, match="longitud"):
        use_case.execute(
            IngestKnowledgeCommand(
                title="Riego",
                topic="papa",
                content="a" * (KnowledgeDocument.CONTENT_MAX_LENGTH + 1),
            )
        )


def test_content_hash_is_deterministic() -> None:
    first = ContentHash.from_content(CONTENT)
    second = ContentHash.from_content(CONTENT)
    other = ContentHash.from_content(CONTENT + " distinto")
    assert first == second
    assert first.value == second.value
    assert first != other
    assert len(first.value) == 64


def test_ingest_knowledge_duplicate_content() -> None:
    use_case, repository = _use_case()
    command = IngestKnowledgeCommand(title="Riego de papa", topic="papa", content=CONTENT)
    use_case.execute(command)
    with pytest.raises(DuplicateKnowledgeDocumentError, match="ya está registrado"):
        use_case.execute(
            IngestKnowledgeCommand(title="Copia de riego", topic="papa", content=CONTENT)
        )
    assert len(repository.documents) == 1


def test_ingest_knowledge_persists_document_and_content() -> None:
    use_case, repository = _use_case()
    result = use_case.execute(
        IngestKnowledgeCommand(title="Riego de papa", topic="papa", content=CONTENT)
    )
    stored = repository.find_by_id(result.id)
    assert stored is not None
    assert stored.title == "Riego de papa"
    assert repository.contents[result.id] == CONTENT.strip()
    assert stored.chunk_count == 0


def test_ingest_knowledge_uses_ports_not_adapters() -> None:
    source = (
        Path(__file__).resolve().parents[1]
        / "app"
        / "application"
        / "useCases"
        / "ingest_knowledge.py"
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    assert "knowledgedocumentrepositoryport" in lowered
    assert "mysqlknowledgedocumentrepository" not in lowered
    assert "externalembeddingadapter" not in lowered


def test_ingest_knowledge_use_case_does_not_import_frameworks_or_sdks() -> None:
    source = (
        Path(__file__).resolve().parents[1]
        / "app"
        / "application"
        / "useCases"
        / "ingest_knowledge.py"
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    forbidden = (
        "fastapi",
        "sqlalchemy",
        "chromadb",
        "openai",
        "anthropic",
        "langchain",
        "httpx",
        "pydantic",
        "import jwt",
        "from jwt",
        "pymysql",
    )
    for item in forbidden:
        assert item not in lowered


def test_ingest_knowledge_does_not_generate_embeddings() -> None:
    source = (
        Path(__file__).resolve().parents[1]
        / "app"
        / "application"
        / "useCases"
        / "ingest_knowledge.py"
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    assert "embeddingport" not in lowered
    assert "embed_text" not in lowered
    assert "embed_texts" not in lowered
    assert "chromadb" not in lowered
    assert "vectorstore" not in lowered
