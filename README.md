# Agro Asistente

Producto Mínimo Viable (PMV1) del curso **Taller de Proyectos 1 – ISI**.

Sistema de asistencia técnica agrícola basado en IA, con RAG básico y arquitectura hexagonal (Ports and Adapters).

## Estado actual

- Fase 1 de scaffolding: frontend, backend, `/health`, MySQL y Git local.
- **HU-01** implementada: registro de agricultor.
- **HU-02** implementada: inicio de sesión con JWT.
- **HU-03** implementada: gestión y selección del contexto agrícola.
- **HU-04** implementada: consulta agrícola en lenguaje natural con respuesta inicial por plantilla.
- **HU-05** implementada: base de conocimiento agrícola (ingesta, hash y duplicados).
- **HU-06** implementada: RAG básico (chunking, embeddings léxicos locales, Chroma, evidencias y respuesta por plantilla).

No hay embeddings semánticos de un proveedor externo, ni SLM, ni RAG avanzado. `ExternalEmbeddingAdapter` queda como punto de sustitución para la Sesión 3.

## HU-01 — Registro de agricultor

- Frontend: [http://localhost:5173/register](http://localhost:5173/register)
- Backend: `POST /api/v1/auth/register`

Flujo:

```text
React /register
    → POST /api/v1/auth/register
    → Auth controller
    → RegisterFarmer (caso de uso)
    → FarmerRepositoryPort + PasswordHasherPort
    → MySQL/MariaDB + bcrypt
```

La contraseña se almacena como hash bcrypt. El correo es único.

## HU-02 — Inicio de sesión

- Frontend: [http://localhost:5173/login](http://localhost:5173/login)
- Backend: `POST /api/v1/auth/login`

Flujo:

```text
React /login
    → POST /api/v1/auth/login
    → Auth controller
    → LoginFarmer (caso de uso)
    → FarmerRepositoryPort + PasswordHasherPort + TokenIssuerPort
    → MariaDB + bcrypt + JWT
```

Si las credenciales son correctas, responde HTTP 200 con `access_token` (JWT), `token_type: bearer` y los datos públicos del agricultor. Credenciales incorrectas: HTTP 401 con `Credenciales inválidas`, sin distinguir email inexistente y contraseña errónea.

El JWT incluye `sub` (id), `email` y `exp`. El secreto y la expiración salen de `JWT_SECRET`, `JWT_ALGORITHM` y `JWT_EXPIRE_MINUTES`.

## HU-03 — Contexto agrícola

- Frontend: [http://localhost:5173/context](http://localhost:5173/context)
- Backend:
  - `GET /api/v1/contexts`
  - `POST /api/v1/contexts`
  - `POST /api/v1/contexts/{id}/select`

Todas las rutas requieren `Authorization: Bearer <JWT>`. El `farmer_id` sale del claim `sub`, no del body.

Campos del contexto (tabla `agricultural_contexts`): `plot_name` (opcional), `crop`, `region`, `notes` (opcional), `is_selected`.

## HU-04 — Consulta agrícola

- Frontend: [http://localhost:5173/query](http://localhost:5173/query)
- Backend: `POST /api/v1/queries`

Flujo:

```text
React /query
    → POST /api/v1/queries  (Authorization: Bearer JWT)
    → Query controller
    → SubmitQuery
    → contexto seleccionado del agricultor (JWT → farmer_id)
    → QueryRepositoryPort
    → tablas queries y responses
    → TextGenerationPort / TemplateGenerationAdapter
    → respuesta inicial por plantilla
```

El `farmer_id` sale del JWT, no del body. La consulta usa únicamente el contexto agrícola seleccionado por ese agricultor. A partir de HU-06, `POST /api/v1/queries` ejecuta recuperación RAG y genera la respuesta inicial con los pasajes recuperados.

## HU-05 — Base de conocimiento agrícola

- Frontend: [http://localhost:5173/knowledge](http://localhost:5173/knowledge)
- Backend:
  - `POST /api/v1/knowledge/ingest`
  - `GET /api/v1/knowledge/documents`

Flujo:

```text
React /knowledge
    → POST /api/v1/knowledge/ingest  (Authorization: Bearer JWT)
    → Knowledge controller
    → IngestKnowledge
    → hash SHA-256 del contenido
    → KnowledgeDocumentRepositoryPort
    → tabla knowledge_documents + archivo Markdown en knowledge/
```

El mismo contenido produce el mismo hash y se rechaza como duplicado (HTTP 409). `chunk_count` queda en 0 hasta indexar con HU-06.

## HU-06 — RAG básico

- Frontend: [http://localhost:5173/query](http://localhost:5173/query)
- Backend:
  - `POST /api/v1/queries` (flujo RAG)
  - `POST /api/v1/knowledge/index` (indexación, JWT)

Flujo:

```text
React /query
    → POST /api/v1/queries  (Authorization: Bearer JWT)
    → SubmitQuery
    → contexto seleccionado
    → RagRetrievalService
    → EmbeddingPort + VectorStorePort
    → Chroma (colección agro_knowledge_pmv1)
    → evidencias
    → TextGenerationPort / TemplateGenerationAdapter
    → tablas queries, responses y evidences
```

Indexación (separada de la ingesta HU-05):

```text
POST /api/v1/knowledge/index
    → IndexKnowledge
    → knowledge/{id}.md → chunks deterministas
    → EmbeddingPort → VectorStorePort → Chroma
```

Los embeddings actuales son **léxicos locales** (`LocalLexicalEmbeddingAdapter`: hashing de tokens). No son embeddings semánticos neuronales ni una API externa de IA. El adaptador `ExternalEmbeddingAdapter` permanece listo para la Sesión 3.

Ver [`docs/INSTALACION.md`](docs/INSTALACION.md) y [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md).

## Estructura

```text
agro-asistente/
├── backend/      FastAPI + dominio + aplicación + infraestructura
├── frontend/     React + Vite
├── database/     schema.sql
├── knowledge/    documentos agrícolas de prueba (HU-05)
└── docs/         instalación y arquitectura
```

## Arranque rápido

Ver la guía completa en [`docs/INSTALACION.md`](docs/INSTALACION.md).

```bash
# Backend (desde backend/)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000

# Frontend (desde frontend/)
npm install
npm run dev
```

Comprobar salud del backend: [http://localhost:8000/health](http://localhost:8000/health)

## Arquitectura

Ver [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md).

El dominio no depende de FastAPI, SQLAlchemy, Chroma ni SDKs de IA. Los servicios externos se aislan detrás de puertos.
