from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import text

from app.application.services.document_chunker import DocumentChunker
from app.application.services.rag_retrieval_service import RagRetrievalService
from app.application.useCases.index_knowledge import IndexKnowledge
from app.application.useCases.submit_query import SubmitQuery
from app.infrastructure.adapters.output.chroma.chroma_vector_store_adapter import (
    ChromaVectorStoreAdapter,
)
from app.infrastructure.adapters.output.embedding.local_lexical_embedding_adapter import (
    LocalLexicalEmbeddingAdapter,
)
from app.infrastructure.adapters.output.mysql.connection import create_mysql_engine
from app.main import app, container

client = TestClient(app)
REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
CONTEXTS_URL = "/api/v1/contexts"
QUERIES_URL = "/api/v1/queries"
INGEST_URL = "/api/v1/knowledge/ingest"
INDEX_URL = "/api/v1/knowledge/index"
QUESTION = "¿Cómo riego la papa en floración para evitar encharcamiento?"


def _register_and_login() -> dict[str, str]:
    payload = {
        "names": "Luis",
        "last_names": "Mamani",
        "email": f"hu06-{uuid4()}@example.com",
        "password": "Password123!",
    }
    register = client.post(REGISTER_URL, json=payload)
    assert register.status_code == 201
    login = client.post(
        LOGIN_URL,
        json={"email": payload["email"], "password": payload["password"]},
    )
    assert login.status_code == 200
    return {
        "token": login.json()["access_token"],
        "farmer_id": login.json()["farmer"]["id"],
    }


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create_and_select_context(token: str) -> dict:
    created = client.post(
        CONTEXTS_URL,
        json={
            "plot_name": "Parcela RAG",
            "crop": "papa",
            "region": "Huancayo",
            "notes": "Prueba HU-06",
        },
        headers=_auth(token),
    )
    assert created.status_code == 201
    selected = client.post(
        f"{CONTEXTS_URL}/{created.json()['id']}/select",
        headers=_auth(token),
    )
    assert selected.status_code == 200
    return selected.json()


def _payload() -> dict[str, str]:
    unique = str(uuid4())
    return {
        "title": f"Riego de papa {unique}",
        "topic": "papa",
        "content": (
            f"# Riego de papa (material de prueba HU-06)\n\n"
            f"Identificador: {unique}.\n\n"
            "La papa en sierra requiere riegos frecuentes en floración.\n\n"
            "Evitar encharcamiento para reducir riesgo de lancha.\n"
        ),
    }


def _cleanup(source_path: str) -> None:
    knowledge_dir = Path(container.settings.knowledge_dir).resolve()
    path = knowledge_dir / Path(source_path).name
    path.unlink(missing_ok=True)


def _rewire_isolated_chroma(tmp_path: Path) -> tuple[object, object, object]:
    original = (
        container.vector_store_port,
        container.rag_retrieval_service,
        container.submit_query_port,
        container.index_knowledge_port,
        container.embedding_port,
    )
    embedding = LocalLexicalEmbeddingAdapter(
        dimension=container.settings.embedding_dimension
    )
    store = ChromaVectorStoreAdapter(
        persist_dir=str(tmp_path / "chroma_http"),
        collection_name="agro_knowledge_pmv1_http_test",
    )
    retrieval = RagRetrievalService(
        embedding_port=embedding,
        vector_store=store,
        top_k=container.settings.rag_top_k,
        min_similarity=container.settings.rag_min_similarity,
    )
    container.embedding_port = embedding
    container.vector_store_port = store
    container.rag_retrieval_service = retrieval
    container.submit_query_port = SubmitQuery(
        query_repository=container.query_repository_port,
        text_generation=container.text_generation_port,
        rag_retrieval=retrieval,
        evidence_repository=container.evidence_repository_port,
    )
    container.index_knowledge_port = IndexKnowledge(
        knowledge_repository=container.knowledge_document_repository_port,
        embedding_port=embedding,
        vector_store=store,
        chunker=DocumentChunker(max_chars=container.settings.chunk_size),
    )
    return original


def _restore_chroma(original: tuple) -> None:
    (
        container.vector_store_port,
        container.rag_retrieval_service,
        container.submit_query_port,
        container.index_knowledge_port,
        container.embedding_port,
    ) = original


def test_index_knowledge_requires_auth() -> None:
    response = client.post(INDEX_URL)
    assert response.status_code == 401


def test_submit_query_without_results_returns_controlled_answer(tmp_path: Path) -> None:
    original = _rewire_isolated_chroma(tmp_path)
    try:
        user = _register_and_login()
        context = _create_and_select_context(user["token"])
        response = client.post(
            QUERIES_URL,
            json={"text": QUESTION},
            headers=_auth(user["token"]),
        )
        assert response.status_code == 201
        body = response.json()
        assert body["context"]["id"] == context["id"]
        assert body["evidences"] == []
        assert "información suficiente" in body["answer"].lower()
        assert "papa" in body["answer"]
        assert "Huancayo" in body["answer"]
        assert body["generation_method"] == "template"
    finally:
        _restore_chroma(original)


def test_submit_query_with_indexed_knowledge_returns_evidences(tmp_path: Path) -> None:
    original = _rewire_isolated_chroma(tmp_path)
    source_path = ""
    query_id = ""
    try:
        user = _register_and_login()
        _create_and_select_context(user["token"])
        payload = _payload()
        ingested = client.post(INGEST_URL, json=payload, headers=_auth(user["token"]))
        assert ingested.status_code == 201
        source_path = ingested.json()["source_path"]
        document_id = ingested.json()["id"]
        unique_marker = payload["title"].split()[-1]

        indexed = client.post(INDEX_URL, headers=_auth(user["token"]))
        assert indexed.status_code == 200
        body_index = indexed.json()
        assert body_index["indexed_documents"] >= 1
        assert body_index["total_chunks"] >= 1
        assert body_index["collection"]

        response = client.post(
            QUERIES_URL,
            json={"text": f"{QUESTION} {unique_marker}"},
            headers=_auth(user["token"]),
        )
        assert response.status_code == 201
        body = response.json()
        query_id = body["id"]
        assert body["evidences"]
        top = body["evidences"][0]
        assert top["document_id"] == document_id
        assert top["excerpt"]
        assert top["similarity_score"] > 0
        assert "base de conocimiento" in body["answer"].lower()
        assert "floración" in body["answer"].lower() or "encharcamiento" in body["answer"].lower()

        engine = create_mysql_engine(container.settings)
        with engine.connect() as connection:
            evidence_row = connection.execute(
                text(
                    "SELECT document_id, excerpt, chroma_chunk_id FROM evidences "
                    "WHERE query_id = :id ORDER BY rank_order ASC"
                ),
                {"id": query_id},
            ).first()
            response_row = connection.execute(
                text("SELECT generation_method FROM responses WHERE query_id = :id"),
                {"id": query_id},
            ).first()
        assert evidence_row is not None
        assert evidence_row[0] == document_id
        assert evidence_row[1]
        assert ":chunk:" in evidence_row[2]
        assert response_row[0] == "template"
    finally:
        if source_path:
            _cleanup(source_path)
        _restore_chroma(original)
