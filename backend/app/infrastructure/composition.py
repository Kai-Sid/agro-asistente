from app.application.services.document_chunker import DocumentChunker
from app.application.services.rag_retrieval_service import RagRetrievalService
from app.application.useCases.create_agricultural_context import CreateAgriculturalContext
from app.application.useCases.index_knowledge import IndexKnowledge
from app.application.useCases.ingest_knowledge import IngestKnowledge
from app.application.useCases.list_agricultural_contexts import ListAgriculturalContexts
from app.application.useCases.list_knowledge_documents import ListKnowledgeDocuments
from app.application.useCases.login_farmer import LoginFarmer
from app.application.useCases.register_farmer import RegisterFarmer
from app.application.useCases.select_agricultural_context import SelectAgriculturalContext
from app.application.useCases.submit_query import SubmitQuery
from app.domain.ports.input.index_knowledge_port import IndexKnowledgePort
from app.domain.ports.input.ingest_knowledge_port import (
    IngestKnowledgePort,
    ListKnowledgeDocumentsPort,
)
from app.domain.ports.input.login_farmer_port import LoginFarmerPort
from app.domain.ports.input.manage_context_port import (
    CreateAgriculturalContextPort,
    ListAgriculturalContextsPort,
    SelectAgriculturalContextPort,
)
from app.domain.ports.input.register_farmer_port import RegisterFarmerPort
from app.domain.ports.input.submit_query_port import SubmitQueryPort
from app.domain.ports.output.agricultural_context_repository_port import (
    AgriculturalContextRepositoryPort,
)
from app.domain.ports.output.embedding_port import EmbeddingPort
from app.domain.ports.output.evidence_repository_port import EvidenceRepositoryPort
from app.domain.ports.output.farmer_repository_port import FarmerRepositoryPort
from app.domain.ports.output.knowledge_document_repository_port import (
    KnowledgeDocumentRepositoryPort,
)
from app.domain.ports.output.password_hasher_port import PasswordHasherPort
from app.domain.ports.output.query_repository_port import QueryRepositoryPort
from app.domain.ports.output.text_generation_port import TextGenerationPort
from app.domain.ports.output.token_issuer_port import TokenIssuerPort
from app.domain.ports.output.token_verifier_port import TokenVerifierPort
from app.domain.ports.output.vector_store_port import VectorStorePort
from app.infrastructure.adapters.output.chroma.chroma_vector_store_adapter import (
    ChromaVectorStoreAdapter,
)
from app.infrastructure.adapters.output.embedding.external_embedding_adapter import (
    ExternalEmbeddingAdapter,
)
from app.infrastructure.adapters.output.embedding.local_lexical_embedding_adapter import (
    LocalLexicalEmbeddingAdapter,
)
from app.infrastructure.adapters.output.generation.template_generation_adapter import (
    TemplateGenerationAdapter,
)
from app.infrastructure.adapters.output.mysql.agricultural_context_repository import (
    MysqlAgriculturalContextRepository,
)
from app.infrastructure.adapters.output.mysql.connection import create_session_factory
from app.infrastructure.adapters.output.mysql.evidence_repository import MysqlEvidenceRepository
from app.infrastructure.adapters.output.mysql.farmer_repository import MysqlFarmerRepository
from app.infrastructure.adapters.output.mysql.knowledge_document_repository import (
    MysqlKnowledgeDocumentRepository,
)
from app.infrastructure.adapters.output.mysql.query_repository import MysqlQueryRepository
from app.infrastructure.adapters.output.security.bcrypt_password_hasher import (
    BcryptPasswordHasher,
)
from app.infrastructure.adapters.output.security.jwt_token_issuer import JwtTokenIssuer
from app.infrastructure.adapters.output.security.jwt_token_verifier import JwtTokenVerifier
from app.infrastructure.config.settings import Settings, get_settings


class CompositionRoot:
    """Cableado de adaptadores. El dominio no conoce esta clase."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.embedding_port: EmbeddingPort = self._build_embedding_port()
        self.password_hasher_port: PasswordHasherPort = BcryptPasswordHasher()
        self.token_issuer_port: TokenIssuerPort = JwtTokenIssuer(
            secret=self.settings.jwt_secret,
            algorithm=self.settings.jwt_algorithm,
            expire_minutes=self.settings.jwt_expire_minutes,
        )
        self.token_verifier_port: TokenVerifierPort = JwtTokenVerifier(
            secret=self.settings.jwt_secret,
            algorithm=self.settings.jwt_algorithm,
        )
        session_factory = create_session_factory(self.settings)
        self.farmer_repository_port: FarmerRepositoryPort = MysqlFarmerRepository(
            session_factory
        )
        self.agricultural_context_repository_port: AgriculturalContextRepositoryPort = (
            MysqlAgriculturalContextRepository(session_factory)
        )
        self.register_farmer_port: RegisterFarmerPort = RegisterFarmer(
            farmer_repository=self.farmer_repository_port,
            password_hasher=self.password_hasher_port,
        )
        self.login_farmer_port: LoginFarmerPort = LoginFarmer(
            farmer_repository=self.farmer_repository_port,
            password_hasher=self.password_hasher_port,
            token_issuer=self.token_issuer_port,
        )
        self.create_agricultural_context_port: CreateAgriculturalContextPort = (
            CreateAgriculturalContext(self.agricultural_context_repository_port)
        )
        self.list_agricultural_contexts_port: ListAgriculturalContextsPort = (
            ListAgriculturalContexts(self.agricultural_context_repository_port)
        )
        self.select_agricultural_context_port: SelectAgriculturalContextPort = (
            SelectAgriculturalContext(self.agricultural_context_repository_port)
        )
        self.text_generation_port: TextGenerationPort = TemplateGenerationAdapter()
        self.query_repository_port: QueryRepositoryPort = MysqlQueryRepository(session_factory)
        self.evidence_repository_port: EvidenceRepositoryPort = MysqlEvidenceRepository(
            session_factory
        )
        self.vector_store_port: VectorStorePort = ChromaVectorStoreAdapter(
            persist_dir=self.settings.chroma_persist_dir,
            collection_name=self.settings.chroma_collection,
        )
        self.rag_retrieval_service = RagRetrievalService(
            embedding_port=self.embedding_port,
            vector_store=self.vector_store_port,
            top_k=self.settings.rag_top_k,
            min_similarity=self.settings.rag_min_similarity,
        )
        self.submit_query_port: SubmitQueryPort = SubmitQuery(
            query_repository=self.query_repository_port,
            text_generation=self.text_generation_port,
            rag_retrieval=self.rag_retrieval_service,
            evidence_repository=self.evidence_repository_port,
        )
        self.knowledge_document_repository_port: KnowledgeDocumentRepositoryPort = (
            MysqlKnowledgeDocumentRepository(
                session_factory,
                knowledge_dir=self.settings.knowledge_dir,
            )
        )
        self.ingest_knowledge_port: IngestKnowledgePort = IngestKnowledge(
            self.knowledge_document_repository_port
        )
        self.list_knowledge_documents_port: ListKnowledgeDocumentsPort = (
            ListKnowledgeDocuments(self.knowledge_document_repository_port)
        )
        self.document_chunker = DocumentChunker(max_chars=self.settings.chunk_size)
        self.index_knowledge_port: IndexKnowledgePort = IndexKnowledge(
            knowledge_repository=self.knowledge_document_repository_port,
            embedding_port=self.embedding_port,
            vector_store=self.vector_store_port,
            chunker=self.document_chunker,
        )

    def _build_embedding_port(self) -> EmbeddingPort:
        provider = (self.settings.embedding_provider or "local").strip().lower()
        if provider == "external":
            return ExternalEmbeddingAdapter(
                api_url=self.settings.embedding_api_url,
                api_key=self.settings.embedding_api_key,
                model=self.settings.embedding_model,
            )
        return LocalLexicalEmbeddingAdapter(dimension=self.settings.embedding_dimension)


def build_container() -> CompositionRoot:
    return CompositionRoot()
