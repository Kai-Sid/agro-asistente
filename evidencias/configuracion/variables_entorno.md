# Variables de entorno

## Alcance

Se analizaron `backend/.env.example`, `backend/app/infrastructure/config/settings.py`, `backend/app/main.py`, `render.yaml`, los archivos bajo `backend/evaluation/` y `backend/tests/`, la configuración del frontend y el uso de `import.meta.env`. Los valores que parezcan secretos reales se muestran como `***`.

## 1. Inventario de variables

| Variable | Obligatoria | Descripción | Valor de ejemplo | Dónde se lee (archivo:línea) | Dónde se declara |
|---|---|---|---|---|---|
| `APP_NAME` | No | Nombre de la aplicación utilizado por FastAPI. | `agro-asistente` | `backend/app/infrastructure/config/settings.py:20`; `backend/app/main.py:22` | `backend/.env.example`; clase `Settings` |
| `APP_ENV` | No | Entorno declarado por la aplicación. | `development` | `backend/app/infrastructure/config/settings.py:21` | `backend/.env.example`; clase `Settings` |
| `API_HOST` | No | Host configurado en la clase de ajustes; el arranque usa una dirección fija documentada. | `127.0.0.1` | `backend/app/infrastructure/config/settings.py:22`; `backend/app/main.py:36-38` | `backend/.env.example`; clase `Settings` |
| `API_PORT` | No | Puerto configurado en los ajustes; el arranque efectivo lee `PORT`. | `8000` | `backend/app/infrastructure/config/settings.py:23`; `backend/app/main.py:42-54` | `backend/.env.example`; clase `Settings` |
| `PORT` | No | Puerto de escucha dinámico del proceso; tiene valor alternativo `8000`. | `8000` | `backend/app/main.py:46-54` | `backend/.env.example`; `render.yaml` lo inyecta según el comentario del entorno |
| `MYSQL_HOST` | No | Host de MySQL/TiDB. Tiene valor local por defecto. | `localhost` o `***` en despliegue externo | `backend/app/infrastructure/config/settings.py:25,102-105` | `backend/.env.example`; `render.yaml:sync:false`; clase `Settings` |
| `MYSQL_PORT` | No | Puerto de conexión a la base de datos. | `3306` local; `4000` Render | `backend/app/infrastructure/config/settings.py:26,106` | `backend/.env.example`; `render.yaml` |
| `MYSQL_USER` | No | Usuario de base de datos. | `root` local; `***` | `backend/app/infrastructure/config/settings.py:27,101` | `backend/.env.example`; `render.yaml:sync:false`; clase `Settings` |
| `MYSQL_PASSWORD` | No | Contraseña de base de datos. | `***` | `backend/app/infrastructure/config/settings.py:28,103-104` | `backend/.env.example`; `render.yaml:sync:false`; clase `Settings` |
| `MYSQL_DATABASE` | No | Nombre de la base de datos. | `agro_asistente` | `backend/app/infrastructure/config/settings.py:29,105-107` | `backend/.env.example`; `render.yaml`; clase `Settings` |
| `JWT_SECRET` | Sí solo para seguridad de producción; No según el arranque aislado | Secreto usado para firmar y verificar JWT. El código tiene un valor fijo inseguro por defecto. | `***` | `backend/app/infrastructure/config/settings.py:31`; `backend/app/infrastructure/composition.py:106-111` | `backend/.env.example`; `render.yaml:sync:false`; clase `Settings` |
| `JWT_ALGORITHM` | No | Algoritmo de emisión y verificación JWT. | `HS256` | `backend/app/infrastructure/config/settings.py:32`; `backend/app/infrastructure/composition.py:106-111` | `backend/.env.example`; `render.yaml`; clase `Settings` |
| `JWT_EXPIRE_MINUTES` | No | Vigencia de los tokens JWT. | `120` | `backend/app/infrastructure/config/settings.py:33`; `backend/app/infrastructure/composition.py:106-111` | `backend/.env.example`; `render.yaml`; clase `Settings` |
| `KNOWLEDGE_DIR` | No | Directorio de documentos de conocimiento. | `../knowledge` | `backend/app/infrastructure/config/settings.py:35`; `backend/app/infrastructure/composition.py:166-169` | `backend/.env.example`; clase `Settings` |
| `CHROMA_PERSIST_DIR` | No | Directorio persistente local de Chroma. | `./chroma_data` | `backend/app/infrastructure/config/settings.py:37`; `backend/app/infrastructure/composition.py:145-149` | `backend/.env.example`; clase `Settings` |
| `CHROMA_COLLECTION` | No | Nombre de la colección vectorial de Chroma. | `agro_knowledge_pmv1` | `backend/app/infrastructure/config/settings.py:38`; `backend/app/infrastructure/composition.py:145-149` | `backend/.env.example`; `render.yaml`; clase `Settings` |
| `RAG_TOP_K` | No | Número máximo de fragmentos recuperados. | `3` | `backend/app/infrastructure/config/settings.py:40`; `backend/app/infrastructure/composition.py:150-154` | `backend/.env.example`; `render.yaml`; clase `Settings` |
| `RAG_MIN_SIMILARITY` | No | Umbral mínimo de similitud RAG. | `0.12` | `backend/app/infrastructure/config/settings.py:41`; `backend/app/infrastructure/composition.py:150-154` | `backend/.env.example`; `render.yaml`; clase `Settings` |
| `CHUNK_SIZE` | No | Tamaño máximo de fragmentos de conocimiento. | `500` | `backend/app/infrastructure/config/settings.py:42`; `backend/app/infrastructure/composition.py:178-181` | `backend/.env.example`; `render.yaml`; clase `Settings` |
| `EMBEDDING_PROVIDER` | No | Selecciona embeddings locales o externos. | `local` | `backend/app/infrastructure/config/settings.py:44`; `backend/app/infrastructure/composition.py:200-204` | `backend/.env.example`; `render.yaml`; clase `Settings` |
| `EMBEDDING_DIMENSION` | No | Dimensión usada por el adaptador léxico local. | `128` | `backend/app/infrastructure/config/settings.py:45`; `backend/app/infrastructure/composition.py:205-206` | `backend/.env.example`; `render.yaml`; clase `Settings` |
| `EMBEDDING_API_URL` | No evidenciado | URL del proveedor externo de embeddings. | No evidenciado | `backend/app/infrastructure/config/settings.py:46`; `backend/app/infrastructure/composition.py:202-203` | `backend/.env.example`; clase `Settings` |
| `EMBEDDING_API_KEY` | No evidenciado | Clave del proveedor externo de embeddings. | `***` | `backend/app/infrastructure/config/settings.py:47`; `backend/app/infrastructure/composition.py:202-203` | `backend/.env.example`; clase `Settings` |
| `EMBEDDING_MODEL` | No evidenciado | Modelo externo de embeddings. | No evidenciado | `backend/app/infrastructure/config/settings.py:48`; `backend/app/infrastructure/composition.py:202-203` | `backend/.env.example`; clase `Settings` |
| `GENERATION_PROVIDER` | No | Selecciona generación mediante plantilla o Ollama. | `ollama` | `backend/app/infrastructure/config/settings.py:50`; `backend/app/infrastructure/composition.py:215-225` | `backend/.env.example`; `render.yaml`; clase `Settings` |
| `OLLAMA_BASE_URL` | No | URL base del servicio Ollama. | `http://127.0.0.1:11434` | `backend/app/infrastructure/config/settings.py:51`; `backend/app/infrastructure/composition.py:225-229` | `backend/.env.example`; `render.yaml:sync:false`; clase `Settings` |
| `OLLAMA_MODEL` | No | Modelo de generación Ollama. | `qwen2.5:1.5b` | `backend/app/infrastructure/config/settings.py:52`; `backend/app/infrastructure/composition.py:225-229`; `backend/evaluation/preflight.py:55-57` | `backend/.env.example`; `render.yaml`; clase `Settings` |
| `OLLAMA_TIMEOUT_SECONDS` | No | Tiempo máximo de espera de Ollama. | `90` | `backend/app/infrastructure/config/settings.py:53`; `backend/app/infrastructure/composition.py:225-229` | `backend/.env.example`; `render.yaml`; clase `Settings` |
| `SENAMHI_WIS2_BASE_URL` | No | URL base de la API SENAMHI WIS 2.0. | `https://wis.senamhi.gob.pe/oapi` | `backend/app/infrastructure/config/settings.py:55`; `backend/app/infrastructure/composition.py:137-141` | `backend/.env.example`; `render.yaml`; clase `Settings` |
| `SENAMHI_WIS2_COLLECTION` | No | Colección meteorológica consultada en WIS 2.0. | `urn:wmo:md:pe-senamhi:synop-hourly` | `backend/app/infrastructure/config/settings.py:56`; `backend/app/infrastructure/composition.py:137-141` | `backend/.env.example`; `render.yaml`; clase `Settings` |
| `SENAMHI_WIS2_TIMEOUT_SECONDS` | No | Tiempo máximo de espera de SENAMHI. | `20` | `backend/app/infrastructure/config/settings.py:57`; `backend/app/infrastructure/composition.py:137-141` | `backend/.env.example`; `render.yaml`; clase `Settings` |
| `CORS_ORIGINS` | No | Lista separada por comas de orígenes CORS permitidos. | `http://localhost:5173` | `backend/app/infrastructure/config/settings.py:59,79-95` | `backend/.env.example`; `render.yaml:sync:false`; clase `Settings` |
| `CLASIFICADOR_MARGEN_MINIMO` | No | Margen mínimo del clasificador HU07. Su cambio fuera de rango detiene el arranque. | `0.17` | `backend/app/infrastructure/config/settings.py:62,68-74`; `backend/app/infrastructure/composition.py:155-161` | `backend/.env.example`; `render.yaml`; clase `Settings` |
| `CLASIFICADOR_MODELO_RUTA` | No | Ruta opcional del modelo del clasificador. Vacío usa el modelo del repositorio. | Ruta relativa o vacío | `backend/app/infrastructure/config/settings.py:63`; `backend/app/infrastructure/composition.py:156-158` | `backend/.env.example` como comentario; clase `Settings` |
| `VITE_API_BASE_URL` | No | URL pública/base usada por el frontend para Axios. Vacío permite URL relativa. | No evidenciado | `frontend/src/api/baseUrl.js:2-7`; `frontend/src/api/client.js:5`; `frontend/src/pages/HomePage.jsx:20` | `render.yaml:sync:false` |
| `RUN_OLLAMA_INTEGRATION_TESTS` | No | Activa una rama de integración de Ollama en pytest. | `true` o `1` | `backend/tests/conftest.py:5-11` | `backend/.env.example` como comentario; no está en `render.yaml` |
| `OLLAMA_INTEGRATION` | No | Variable alternativa utilizada por pytest para activar la integración Ollama. | `1`, `true` o `yes` | `backend/tests/conftest.py:6-10` | No evidenciado en ejemplo o infraestructura |
| `SENAMHI_WIS2_INTEGRATION` | No | Activa el test real de integración SENAMHI. | `1` | `backend/tests/test_senamhi_wis2_integration.py:14-17` | No evidenciado en ejemplo o infraestructura |
| `RAGAS_LLM_PROVIDER` | No por defecto Ollama | Selecciona Ollama o OpenAI como juez RAGAS. | `ollama` | `backend/evaluation/preflight.py:64`; `backend/evaluation/ragas_runner.py:31,60-64` | `backend/.env.example` como comentario; no en `render.yaml` |
| `RAGAS_OPENAI_MODEL` | No | Modelo OpenAI opcional para RAGAS. | `gpt-4o-mini` | `backend/evaluation/ragas_runner.py:31` | No evidenciado en ejemplo o infraestructura |
| `RAGAS_EMBEDDING_MODEL` | No | Modelo de embeddings usado por RAGAS. | `text-embedding-3-small` o nombre Ollama | `backend/evaluation/ragas_runner.py:32,45` | `backend/.env.example` como comentario; no en `render.yaml` |
| `OPENAI_API_KEY` | Sí si `RAGAS_LLM_PROVIDER=openai` | Clave del proveedor OpenAI usada por RAGAS. | `***` | `backend/evaluation/ragas_runner.py:60-64` | `backend/.env.example` como comentario; no en `render.yaml` |
| `RAGAS_OLLAMA_API_KEY` | No | Clave/API key usada por el cliente compatible OpenAI de Ollama. Tiene valor alternativo `ollama`. | `***` o `ollama` | `backend/evaluation/ragas_runner.py:136` | No evidenciado en ejemplo o infraestructura |

## 2. Clasificación

### Secretos y tokens

- `JWT_SECRET`
- `MYSQL_PASSWORD`
- `EMBEDDING_API_KEY`
- `OPENAI_API_KEY`
- `RAGAS_OLLAMA_API_KEY`
- `MYSQL_USER` y `MYSQL_HOST` no son secretos por sí mismos, pero pueden identificarse como datos de conexión y están fuera del repositorio en Render.

### Configuración de base de datos

- `MYSQL_HOST`
- `MYSQL_PORT`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_DATABASE`

### Configuración de APIs o servicios externos

- `EMBEDDING_PROVIDER`
- `EMBEDDING_API_URL`
- `EMBEDDING_API_KEY`
- `EMBEDDING_MODEL`
- `GENERATION_PROVIDER`
- `OLLAMA_BASE_URL`
- `OLLAMA_MODEL`
- `OLLAMA_TIMEOUT_SECONDS`
- `SENAMHI_WIS2_BASE_URL`
- `SENAMHI_WIS2_COLLECTION`
- `SENAMHI_WIS2_TIMEOUT_SECONDS`
- `RAGAS_LLM_PROVIDER`
- `RAGAS_OPENAI_MODEL`
- `RAGAS_EMBEDDING_MODEL`
- `OPENAI_API_KEY`
- `RAGAS_OLLAMA_API_KEY`
- `VITE_API_BASE_URL`

### Configuración general

- `APP_NAME`
- `APP_ENV`
- `API_HOST`
- `API_PORT`
- `PORT`
- `JWT_ALGORITHM`
- `JWT_EXPIRE_MINUTES`
- `KNOWLEDGE_DIR`
- `CHROMA_PERSIST_DIR`
- `CHROMA_COLLECTION`
- `RAG_TOP_K`
- `RAG_MIN_SIMILARITY`
- `CHUNK_SIZE`
- `EMBEDDING_DIMENSION`
- `CORS_ORIGINS`
- `CLASIFICADOR_MARGEN_MINIMO`
- `CLASIFICADOR_MODELO_RUTA`
- `RUN_OLLAMA_INTEGRATION_TESTS`
- `OLLAMA_INTEGRATION`
- `SENAMHI_WIS2_INTEGRATION`

## 3. Variables usadas pero no declaradas

| Variable usada | Evidencia de uso | Declaración encontrada |
|---|---|---|
| `OLLAMA_INTEGRATION` | `backend/tests/conftest.py:6-10` | No evidenciada |
| `SENAMHI_WIS2_INTEGRATION` | `backend/tests/test_senamhi_wis2_integration.py:14-17` | No evidenciada |
| `RAGAS_OPENAI_MODEL` | `backend/evaluation/ragas_runner.py:31` | No evidenciada |
| `RAGAS_OLLAMA_API_KEY` | `backend/evaluation/ragas_runner.py:136` | No evidenciada |

## Variables declaradas pero no usadas por el flujo principal

| Variable | Evidencia de declaración | Uso observado |
|---|---|---|
| `API_HOST` | `backend/.env.example`; clase `Settings:22` | Solo se expone como ajuste; `backend/app/main.py` usa `0.0.0.0` fijo para producción |
| `API_PORT` | `backend/.env.example`; clase `Settings:23` | Solo se expone como ajuste; `backend/app/main.py` usa `PORT` y luego `8000` |
| `EMBEDDING_API_URL`, `EMBEDDING_API_KEY`, `EMBEDDING_MODEL` | `backend/.env.example`; clase `Settings:46-48` | Se pasan al adaptador externo, pero este no ejecuta aún un proveedor concreto |
| `CLASIFICADOR_MODELO_RUTA` | `backend/.env.example` como comentario; clase `Settings:63` | Sí tiene uso por el adaptador en `backend/app/infrastructure/composition.py:156-158`; no es una variable declarada/no usada |
| `RAGAS_*` comentadas en `.env.example` | `backend/.env.example` | Las variables usadas por el evaluador pueden depender de entorno directo y no de `Settings` |

## 4. Riesgos de seguridad

| Riesgo | Evidencia | Impacto potencial |
|---|---|---|
| JWT con secreto fijo inseguro por defecto | `backend/app/infrastructure/config/settings.py:31` contiene `change-me-in-local-env-do-not-use-in-production` | Si producción conserva el valor, los tokens podrían ser falsificables por cualquier persona que conozca el repositorio |
| Credenciales reales en un script versionado | `insertar_datos.py` contiene valores fijos de conexión a TiDB Cloud | Los secretos deben tratarse como `***`, rotarse y eliminarse del historial/versionado |
| Contraseña de base de datos vacía en el ejemplo | `backend/.env.example:16-19` declara `MYSQL_PASSWORD=` | Puede producir una configuración insegura si se lleva a producción sin secret management |
| JWT vacío en el ejemplo | `backend/.env.example:22` declara `JWT_SECRET=` | Si no se reemplaza por Render o el entorno, prevalece el valor por defecto fijo |
| CORS limitado a un origen local por defecto | `backend/app/infrastructure/config/settings.py:59,79-95` | Es seguro por defecto, pero puede no permitir el frontend desplegado salvo configuración externa |
| Reglas CORS que excluyen comodines | `backend/app/infrastructure/config/settings.py:79-95` evita un comodín suelto y permite solo el dominio exacto más subdominios HTTPS de un nivel | No se encontró evidencia de CORS abierto mediante `*`; no debe asumirse que existe |
| Variables RAGAS externas no declaradas | `RAGAS_OPENAI_MODEL`, `RAGAS_OLLAMA_API_KEY` y `OPENAI_API_KEY` se usan sin configuración central completa | Riesgo de configuración incompleta y posible uso de una clave en el entorno del evaluador |
| Contratos externos sin obligatoriedad garantizada | `EMBEDDING_API_URL`, `EMBEDDING_API_KEY` y `EMBEDDING_MODEL` tienen valores vacíos por defecto y el adaptador externo no está implementado | Si se activa `EMBEDDING_PROVIDER=external`, el código no demuestra que las variables falten se validen al arrancar |
| Puertos/hosts locales como configuración persistente | `API_HOST=127.0.0.1`, `OLLAMA_BASE_URL=http://127.0.0.1:11434` | Pueden impedir despliegue o comunicación remota si no se sobrescriben; no es por sí mismo una vulnerabilidad |
| Uso de datos de prueba para base de datos | `insertar_datos.py` trunca tablas y carga datos falsos | Riesgo operativo si se ejecuta sobre producción, además de que las credenciales fijas deben retirarse |
