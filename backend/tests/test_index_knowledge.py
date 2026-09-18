from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.application.services.document_chunker import DocumentChunker
from app.application.useCases.index_knowledge import IndexKnowledge
from app.domain.entities.knowledge_document import KnowledgeDocument
from app.domain.ports.output.embedding_port import EmbeddingPort
from app.domain.ports.output.knowledge_document_repository_port import (
    KnowledgeDocumentRepositoryPort,
)
from app.domain.ports.output.vector_store_port import VectorRecord, VectorSearchHit, VectorStorePort
from app.domain.valueObjects.content_hash import ContentHash
from app.infrastructure.adapters.output.embedding.local_lexical_embedding_adapter import (
    LocalLexicalEmbeddingAdapter,
)

CONTENT = """# Riego de papa

La papa en sierra requiere riegos frecuentes en floración.
Evitar encharcamiento para reducir riesgo de lancha.
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


class InMemoryVectorStore(VectorStorePort):
    def __init__(self) -> None:
        self.records: dict[str, VectorRecord] = {}

    def upsert(self, records: list[VectorRecord]) -> None:
        for record in records:
            self.records[record.id] = record

    def similarity_search(self, embedding: list[float], top_k: int) -> list[VectorSearchHit]:
        hits: list[VectorSearchHit] = []
        for record in self.records.values():
            score = _cosine(embedding, record.embedding)
            hits.append(
                VectorSearchHit(
                    id=record.id,
                    content=record.content,
                    metadata=record.metadata,
                    similarity=score,
                )
            )
        hits.sort(key=lambda item: item.similarity, reverse=True)
        return hits[:top_k]


def _cosine(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=True))


def _document(content: str = CONTENT) -> KnowledgeDocument:
    return KnowledgeDocument(
        document_id=str(uuid4()),
        title="Riego de papa",
        source_path="knowledge/demo.md",
        topic="papa",
        content_hash=ContentHash.from_content(content),
        chunk_count=0,
        ingested_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )


def test_index_knowledge_upserts_chunks_with_deterministic_ids() -> None:
    repository = InMemoryKnowledgeRepository()
    store = InMemoryVectorStore()
    document = _document()
    repository.save(document, CONTENT)
    use_case = IndexKnowledge(
        knowledge_repository=repository,
        embedding_port=LocalLexicalEmbeddingAdapter(dimension=32),
        vector_store=store,
        chunker=DocumentChunker(max_chars=80),
    )

    result = use_case.execute()

    assert result.indexed_documents == 1
    assert result.total_chunks == len(store.records)
    assert result.total_chunks >= 1
    assert document.chunk_count == result.total_chunks
    assert all(":chunk:" in chunk_id for chunk_id in store.records)


def test_index_knowledge_duplicate_document_does_not_duplicate_chunks() -> None:
    repository = InMemoryKnowledgeRepository()
    store = InMemoryVectorStore()
    document = _document()
    repository.save(document, CONTENT)
    use_case = IndexKnowledge(
        knowledge_repository=repository,
        embedding_port=LocalLexicalEmbeddingAdapter(dimension=32),
        vector_store=store,
        chunker=DocumentChunker(max_chars=80),
    )

    first = use_case.execute()
    ids_after_first = set(store.records)
    second = use_case.execute()

    assert first.total_chunks == second.total_chunks
    assert set(store.records) == ids_after_first
    assert len(store.records) == first.total_chunks


def test_index_knowledge_uses_embedding_port_not_sdk() -> None:
    source = (
        Path(__file__).resolve().parents[1]
        / "app"
        / "application"
        / "useCases"
        / "index_knowledge.py"
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    assert "embeddingport" in lowered
    assert "vectorstoreport" in lowered
    assert "chromadb" not in lowered
    assert "chromavectorstoreadapter" not in lowered
    assert "openai" not in lowered
    assert "httpx" not in lowered
    assert "fastapi" not in lowered


def test_index_knowledge_does_not_depend_on_concrete_embedding_adapter() -> None:
    class CountingEmbedding(EmbeddingPort):
        def __init__(self) -> None:
            self.calls = 0

        def embed_text(self, text: str) -> list[float]:
            return self.embed_texts([text])[0]

        def embed_texts(self, texts: list[str]) -> list[list[float]]:
            self.calls += 1
            return LocalLexicalEmbeddingAdapter(dimension=16).embed_texts(texts)

    repository = InMemoryKnowledgeRepository()
    store = InMemoryVectorStore()
    repository.save(_document(), CONTENT)
    embedding = CountingEmbedding()
    use_case = IndexKnowledge(
        knowledge_repository=repository,
        embedding_port=embedding,
        vector_store=store,
        chunker=DocumentChunker(max_chars=120),
    )
    result = use_case.execute()
    assert embedding.calls == 1
    assert result.total_chunks == len(store.records)
