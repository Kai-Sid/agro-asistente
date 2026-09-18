-- Agro Asistente PMV1
-- Esquema reproducible para MySQL 8
-- Collation unicode para compatibilidad con MySQL 8 y MariaDB de desarrollo local.

CREATE DATABASE IF NOT EXISTS agro_asistente
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE agro_asistente;

CREATE TABLE IF NOT EXISTS farmers (
    id CHAR(36) NOT NULL,
    full_name VARCHAR(120) NOT NULL,
    email VARCHAR(190) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_farmers_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS agricultural_contexts (
    id CHAR(36) NOT NULL,
    farmer_id CHAR(36) NOT NULL,
    plot_name VARCHAR(120) NULL,
    crop VARCHAR(50) NOT NULL,
    region VARCHAR(120) NOT NULL,
    notes VARCHAR(500) NULL,
    is_selected TINYINT(1) NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    KEY idx_contexts_farmer (farmer_id),
    CONSTRAINT fk_contexts_farmer
        FOREIGN KEY (farmer_id) REFERENCES farmers (id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS queries (
    id CHAR(36) NOT NULL,
    farmer_id CHAR(36) NOT NULL,
    context_id CHAR(36) NOT NULL,
    question_text TEXT NOT NULL,
    created_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    KEY idx_queries_farmer (farmer_id),
    KEY idx_queries_context (context_id),
    CONSTRAINT fk_queries_farmer
        FOREIGN KEY (farmer_id) REFERENCES farmers (id)
        ON DELETE CASCADE,
    CONSTRAINT fk_queries_context
        FOREIGN KEY (context_id) REFERENCES agricultural_contexts (id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS responses (
    id CHAR(36) NOT NULL,
    query_id CHAR(36) NOT NULL,
    answer_text TEXT NOT NULL,
    generation_method VARCHAR(40) NOT NULL,
    created_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_responses_query (query_id),
    CONSTRAINT fk_responses_query
        FOREIGN KEY (query_id) REFERENCES queries (id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS knowledge_documents (
    id CHAR(36) NOT NULL,
    title VARCHAR(200) NOT NULL,
    source_path VARCHAR(255) NOT NULL,
    topic VARCHAR(50) NOT NULL,
    content_hash CHAR(64) NOT NULL,
    chunk_count INT NOT NULL,
    ingested_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_knowledge_content_hash (content_hash)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS evidences (
    id CHAR(36) NOT NULL,
    query_id CHAR(36) NOT NULL,
    response_id CHAR(36) NOT NULL,
    document_id CHAR(36) NOT NULL,
    chroma_chunk_id VARCHAR(120) NOT NULL,
    excerpt TEXT NOT NULL,
    similarity_score DECIMAL(6,5) NOT NULL,
    rank_order INT NOT NULL,
    PRIMARY KEY (id),
    KEY idx_evidences_query (query_id),
    KEY idx_evidences_response (response_id),
    KEY idx_evidences_document (document_id),
    CONSTRAINT fk_evidences_query
        FOREIGN KEY (query_id) REFERENCES queries (id)
        ON DELETE CASCADE,
    CONSTRAINT fk_evidences_response
        FOREIGN KEY (response_id) REFERENCES responses (id)
        ON DELETE CASCADE,
    CONSTRAINT fk_evidences_document
        FOREIGN KEY (document_id) REFERENCES knowledge_documents (id)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
