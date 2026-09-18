from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.application.services.document_chunker import DocumentChunker, make_chunk_id
from app.domain.entities.knowledge_document import KnowledgeDocument
from app.domain.valueObjects.content_hash import ContentHash

CONTENT = """# Riego de papa

La papa en sierra requiere riegos frecuentes en floración.

Evitar encharcamiento para reducir riesgo de lancha.

Registrar el contexto agrícola del agricultor.
"""


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


def test_document_is_split_into_chunks() -> None:
    chunker = DocumentChunker(max_chars=80)
    chunks = chunker.chunk(CONTENT, _document())
    assert len(chunks) >= 2
    joined = " ".join(item.content for item in chunks)
    assert "floración" in joined
    assert "encharcamiento" in joined
    assert all(item.document_id == chunks[0].document_id for item in chunks)
    assert [item.chunk_index for item in chunks] == list(range(len(chunks)))


def test_chunk_ids_are_deterministic() -> None:
    document = _document()
    chunker = DocumentChunker(max_chars=80)
    first = chunker.chunk(CONTENT, document)
    second = chunker.chunk(CONTENT, document)
    assert [item.chunk_id for item in first] == [item.chunk_id for item in second]
    assert first[0].chunk_id == make_chunk_id(document.content_hash.value, 0)
    assert first[0].chunk_id.startswith(document.content_hash.value)


def test_changed_content_changes_chunk_ids() -> None:
    original = _document(CONTENT)
    changed_content = CONTENT + "\n\nNuevo párrafo sobre abonamiento."
    changed = _document(changed_content)
    chunker = DocumentChunker(max_chars=80)
    original_ids = {item.chunk_id for item in chunker.chunk(CONTENT, original)}
    changed_ids = {item.chunk_id for item in chunker.chunk(changed_content, changed)}
    assert original.content_hash != changed.content_hash
    assert original_ids.isdisjoint(changed_ids)


def test_chunker_does_not_import_chroma() -> None:
    source = (
        Path(__file__).resolve().parents[1]
        / "app"
        / "application"
        / "services"
        / "document_chunker.py"
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    assert "chromadb" not in lowered
    assert "chroma" not in lowered
    assert "openai" not in lowered
