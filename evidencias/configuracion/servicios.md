# Servicios y orden de arranque

## 1. Inventario de servicios

| Servicio | Tipo | Local o remoto | Obligatorio | Puerto/URL | Variables que lo configuran | Evidencia (archivo:línea) |
|---|---|---|---|---|---|---|
| API de Agro Asistente | API/servidor web | Local o remoto según despliegue | Sí para consumir el backend | Puerto local `8000` o variable `PORT`; producción escucha en todas las interfaces | `PORT` (usada en el arranque); `API_HOST` y `API_PORT` (declaradas en settings.py, sin uso evidenciado en el arranque) | `backend/app/main.py:36-54`; `backend/.env.example:3-10`; `render.yaml:5-12`; `backend/app/infrastructure/config/settings.py:22-23` |
| Frontend React/Vite | Hosting estático | Local o remoto según despliegue | Sí para usar la interfaz web | Local `5173`; URL pública de Render: No evidenciado | `VITE_API_BASE_URL` | `frontend/vite.config.js:4-11`; `frontend/.env.example:1-5`; `render.yaml:66-75` |
| MySQL | Base de datos MySQL-compatible; TiDB Cloud según el .env local (no versionado) | Remoto o local según configuración | Sí para operaciones persistentes; el arranque conserva salud aunque no haya conexión | Local 3306; Render declara MYSQL_PORT=4000; host remoto: No evidenciado en archivos versionados | `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE` | `backend/.env.example:13-19`; `backend/app/infrastructure/config/settings.py:25-29,101-112`; `backend/app/infrastructure/adapters/output/mysql/connection.py:8-24`; `render.yaml:37-42,52-56`; `docs/INSTALACION.md:31-48`; `backend/.env:7-8 (archivo local no versionado)` |
| Chroma | Almacén vectorial | Local | Sí para indexar y recuperar el RAG; el adaptador usa almacenamiento persistente local | Puerto/URL: No evidenciado; usa directorio local configurable | `CHROMA_PERSIST_DIR`, `CHROMA_COLLECTION` | `backend/.env.example:21-23`; `backend/app/infrastructure/config/settings.py:37-38`; `backend/app/infrastructure/adapters/output/chroma/chroma_vector_store_adapter.py:1-29`; `backend/app/infrastructure/composition.py:145-154` |
| Ollama | Servidor de modelo de lenguaje | Local por defecto; remoto si se configura | Sí para generación Ollama PMV1; puede usarse el adaptador plantilla solo en pruebas | `http://127.0.0.1:11434` local; URL remota: No evidenciado | `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `OLLAMA_TIMEOUT_SECONDS`, `GENERATION_PROVIDER` | `backend/.env.example:37-43`; `backend/app/infrastructure/config/settings.py:50-53`; `backend/app/infrastructure/adapters/output/generation/adaptador_generacion_ollama.py:48-92`; `backend/app/infrastructure/composition.py:215-229`; `render.yaml:16-19,64` |
| SENAMHI WIS 2.0 | API externa meteorológica | Remoto | No evidenciado como obligatorio para el arranque; sí para obtener observaciones meteorológicas | `https://wis.senamhi.gob.pe/oapi` | `SENAMHI_WIS2_BASE_URL`, `SENAMHI_WIS2_COLLECTION`, `SENAMHI_WIS2_TIMEOUT_SECONDS` | `backend/.env.example:46-50`; `backend/app/infrastructure/config/settings.py:55-57`; `backend/app/infrastructure/adapters/output/senamhi/adaptador_senamhi_wis2.py:19-45`; `render.yaml:44-50`; `backend/app/infrastructure/composition.py:137-141` |
| Proveedor externo de embeddings | API externa de embeddings | Remoto | No evidenciado; el proveedor concreto no está implementado | URL: No evidenciado | `EMBEDDING_PROVIDER`, `EMBEDDING_API_URL`, `EMBEDDING_API_KEY`, `EMBEDDING_MODEL` | `backend/.env.example:32-35`; `backend/app/infrastructure/config/settings.py:44-48`; `backend/app/infrastructure/adapters/output/embedding/external_embedding_adapter.py:7-38`; `backend/app/infrastructure/composition.py:200-204` |
| Embeddings locales léxicos | Otro (procesamiento local) | Local | Sí mientras `EMBEDDING_PROVIDER=local` | No usa puerto ni URL | `EMBEDDING_PROVIDER`, `EMBEDDING_DIMENSION` | `backend/.env.example:32-34`; `backend/app/infrastructure/config/settings.py:44-45`; `backend/app/infrastructure/composition.py:200-206`; `render.yaml:20-21` |
| Render | Hosting | Remoto | Sí solo para el despliegue descrito en el Blueprint | No define URL pública concreta | Variables declaradas en `render.yaml` | `render.yaml:1-75` |
| RAGAS | Otro (evaluación/juez LLM) | Local o remoto según proveedor; Ollama es el default documentado | No evidenciado para el funcionamiento del API principal | Ollama compatible `/v1`: depende de `OLLAMA_BASE_URL`; OpenAI: URL/puerto no evidenciado | `RAGAS_LLM_PROVIDER`, `RAGAS_OPENAI_MODEL`, `RAGAS_EMBEDDING_MODEL`, `OPENAI_API_KEY`, `RAGAS_OLLAMA_API_KEY` | `backend/.env.example:52-55`; `backend/evaluation/preflight.py:64`; `backend/evaluation/ragas_runner.py:25-64,128-136`; `docs/ARQUITECTURA.md` sección “Evaluación RAGAS” |

## 2. Orden de arranque

La evidencia demuestra esta secuencia de instalación local:

1. Crear el entorno backend e instalar `backend/requirements.txt`: `docs/INSTALACION.md:11-22`.
2. Crear MySQL y aplicar `database/schema.sql` antes de probar registros y otras operaciones persistentes: `docs/INSTALACION.md:31-48`.
3. Configurar e iniciar Ollama con el modelo `qwen2.5:1.5b` antes de una consulta que requiera generación Ollama: `backend/.env.example:37-43`; `docs/INSTALACION.md:99-124`.
4. Iniciar el backend con `uvicorn app.main:app --reload --host 127.0.0.1 --port 8000` o el arranque configurado por `PORT`: `docs/INSTALACION.md:24-29`; `backend/app/main.py:42-54`.
5. Iniciar Vite en el frontend para que el proxy envíe `/health` y `/api` al backend: `frontend/vite.config.js:4-11`; `docs/INSTALACION.md:50-55`.

No está evidenciado un orden obligatorio entre MySQL, Chroma y Ollama al momento de iniciar el proceso. Sí hay evidencia de dependencias funcionales:

- El modelo de lenguaje debe estar activo antes de responder una consulta Ollama: `docs/INSTALACION.md:99-124`; `backend/app/infrastructure/adapters/output/generation/adaptador_generacion_ollama.py:70-92`.
- Chroma debe estar disponible o inicializable antes de indexar documentos y recuperar evidencia RAG: `backend/app/infrastructure/adapters/output/chroma/chroma_vector_store_adapter.py:19-29`; `backend/app/infrastructure/composition.py:145-154`.
- El frontend consume el backend a través del proxy local o `VITE_API_BASE_URL`: `frontend/vite.config.js:7-10`; `frontend/src/api/client.js:5`.

## 3. Servicios que requieren cuenta, clave o descarga previa

| Servicio/recurso | Requisito previo evidenciado | Evidencia |
|---|---|---|
| Ollama | Descargar el modelo configurado previamente; el proyecto indica `ollama pull qwen2.5:1.5b` | `backend/.env.example:37-43`; `backend/app/infrastructure/adapters/output/generation/adaptador_generacion_ollama.py:70-92` |
| OpenAI, si se selecciona para RAGAS | Requiere `OPENAI_API_KEY` cuando `RAGAS_LLM_PROVIDER=openai`; no se especifica una cuenta ni el proceso de creación | `backend/.env.example:52-55`; `backend/evaluation/ragas_runner.py:25-64` |
| Proveedor externo de embeddings | Puede requerir una clave y cuenta según el proveedor, pero el proveedor concreto no está seleccionado ni evidenciado | `backend/app/infrastructure/adapters/output/embedding/external_embedding_adapter.py:7-38` |
| MySQL/TiDB | Requiere host, usuario y contraseña configurados en el entorno; la cuenta específica no está evidenciada | `backend/.env.example:13-19`; `render.yaml:52-56` |
| SENAMHI WIS 2.0 | No evidencia requerir cuenta, clave o descarga previa; el `.env.example` declara que no usa API key | `backend/.env.example:46-50` |
| Render | No se evidencia qué cuenta o credenciales requiere para el usuario; el Blueprint contiene variables que se completan fuera del repositorio | `render.yaml:1-3` |
| RAGAS con Ollama | No se evidencia una clave; el cliente usa una clave literal de compatibilidad `ollama` y Ollama local/remoto según `OLLAMA_BASE_URL` | `backend/evaluation/ragas_runner.py:128-136` |

## 4. Diferencias entre documentación y código

### Documentado pero sin evidencia suficiente en el código

- `Google Colab Pro` aparece como ejecución opcional de RAGAS, pero no hay evidencia de integración o configuración requerida en el código: `docs/ARQUITECTURA.md` sección “Evaluación RAGAS”.
- El identificador histórico de `Qwen2.5 1.8B` está documentado, pero el código usa por defecto el tag `qwen2.5:1.5b`: `docs/ARQUITECTURA.md` sección “Generación de texto”; `backend/.env.example:37-43`; `backend/app/infrastructure/config/settings.py:52`.
- Docker, Docker Compose y CI/CD aparecen como propuestas o ausencias no implementadas en las evidencias; no se encontró configuración ejecutable en el repositorio: `evidencias/dependencias/infraestructura.md` sección 7.
- Una URL pública concreta de Render para el frontend o API no está evidenciada en `render.yaml`; solo se define el Blueprint y una URL de ejemplo usada por pruebas: `render.yaml:66-75`; `frontend/src/api/conexion.test.js:5-8`.
- La documentación menciona tablas con nombres ingleses como `farmers`, `agricultural_contexts`, `queries` y `responses`; el esquema versionado crea tablas españolas: `agricultores`, `contextos_agricolas`, `consultas`, `respuestas`, `documentos_conocimiento`, `evidencias`: `docs/ARQUITECTURA.md` secciones HU-01 a HU-04; `database/schema.sql:5-82`.

### En el código pero no documentado

- El adaptador SENAMHI WIS 2.0 existe en el backend y consume `https://wis.senamhi.gob.pe/oapi`, pero esta integración no aparece como servicio central en `docs/ARQUITECTURA.md`: `backend/app/infrastructure/adapters/output/senamhi/adaptador_senamhi_wis2.py:19-45`; `backend/app/infrastructure/config/settings.py:55-57`.
- El almacenamiento persistente y configurable de Chroma se construye con `PersistentClient` y telemetría desactivada; la documentación solo declara Chroma y su colección: `backend/app/infrastructure/adapters/output/chroma/chroma_vector_store_adapter.py:1-29`; `docs/ARQUITECTURA.md` sección “Persistencia”.
- El puerto dinámico `PORT` y el fallback `8000` están implementados en el arranque; la guía local usa directamente `8000`: `backend/app/main.py:42-54`; `docs/INSTALACION.md:24-29`.
- El adaptador externo de embeddings está preparado como placeholder y acepta variables de entorno, pero no aparece como servicio operativo en las guías de instalación: `backend/app/infrastructure/adapters/output/embedding/external_embedding_adapter.py:7-38`; `backend/.env.example:32-35`.
- RAGAS contiene proveedores Ollama y OpenAI configurables mediante variables usadas directamente por el evaluador; esta ejecución no está incluida como requisito de arranque del API: `backend/evaluation/ragas_runner.py:25-64,128-136`; `backend/evaluation/preflight.py:64`.
- TiDB Cloud como base de datos real aparece solo en la configuración local no versionada (backend/.env:7-8); no figura en render.yaml ni en docs/.
