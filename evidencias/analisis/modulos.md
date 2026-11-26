# Módulos del sistema (Fase 5)

## Alcance y método

- **Fuentes:** `backend/app`, `backend/tests`, `frontend/src`, `database/schema.sql`, `render.yaml` y análisis automático de imports con AST.
- **Commit base del código:** `eaac3da`.
- **Regla:** solo se registra lo evidenciado. Lo no leído en detalle figura como «No leído».

## 1. Tamaño del código

| Parte | Archivos | Líneas |
|---|---|---|
| `backend/app/domain` | 65 | 2 073 |
| `backend/app/application` | 30 | 1 714 |
| `backend/app/infrastructure` | 52 | 3 361 |
| `backend/app/main.py` y `app/__init__.py` | 2 | 65 |
| **Total backend (aplicación)** | **149** | **7 213** |
| `backend/tests` | 33 archivos de prueba | 4 941 |
| `frontend/src` (js y jsx) | 26 | 1 951 |

## 2. Módulos funcionales del backend

| Módulo | Caso de uso (aplicación) | Entidades y objetos de valor | Adaptador de entrada | Adaptadores de salida |
|---|---|---|---|---|
| Autenticación | `RegistrarAgricultor`, `IniciarSesionAgricultor` | `Agricultor`, `Email`, `HashContrasena` | `auth_controller.py`, `dependencia_autenticacion.py` | `repositorio_agricultor` (MySQL), `hasher_contrasena_bcrypt`, `emisor_token_jwt`, `verificador_token_jwt` |
| Contextos agrícolas | `CrearContextoAgricola`, `ListarContextosAgricolas`, `SeleccionarContextoAgricola` | `ContextoAgricola`, `Cultivo`, `Region` | `context_controller.py` | `repositorio_contexto_agricola` (MySQL) |
| Consulta con RAG | `RegistrarConsulta` (con `ServicioRecuperacionRag` y `suficiencia_contexto`) | `Consulta`, `Respuesta`, `Evidencia`, `TextoConsulta` | `query_controller.py` | `repositorio_consulta`, `repositorio_evidencia` (MySQL), `chroma_vector_store_adapter`, `local_lexical_embedding_adapter`, `adaptador_generacion_ollama` |
| Base de conocimiento | `IncorporarConocimiento`, `IndexarConocimiento`, `ListarDocumentosConocimiento`, `FragmentadorDocumentos` | `DocumentoConocimiento`, `HashContenido` | `knowledge_controller.py` | `repositorio_documento_conocimiento` (MySQL y archivos), Chroma, embeddings |
| Clasificación de consultas | `ClasificarConsulta` | (resultado de clasificación en el puerto) | `clasificacion_controller.py` | `adaptador_clasificador_tfidf` (modelo `.joblib`) |
| Riesgo experimental | `PredecirRiesgoAgricola` | `EscenarioRiesgo` (en el puerto) | `riesgo_controller.py` | `adaptador_predictor_riesgo` (modelo `.joblib`) |
| Clima | `ObtenerObservacionesMeteorologicas` | `ObservacionMeteorologica` | `weather_controller.py` | `adaptador_senamhi_wis2` (HTTP) |
| Salud | — | — | `health_controller.py` | `ping_mysql` |
| Configuración y arranque | — | — | `main.py` | `composition.py`, `settings.py`, `cors.py` |

## 3. Módulos del frontend

| Módulo | Archivos | Función |
|---|---|---|
| Acceso público | `HomePage`, `LoginPage`, `RegisterPage`, `PublicShell`, `PublicHeader` | Inicio, login y registro |
| Zona autenticada | `DashboardPage`, `AuthenticatedShell`, `AppHeader`, `AuthFooter`, `ProtectedRoute` | Panel y menú: Dashboard, Contexto, Consulta, Base de conocimiento, Riesgo experimental, Cerrar sesión |
| Contexto | `ContextPage` | Crear, listar y seleccionar contextos |
| Consulta | `QueryPage`, `consulta/presentacion.js` | Enviar consultas y mostrar respuesta y evidencias |
| Conocimiento | `KnowledgePage` | Listar e ingerir documentos |
| Riesgo | `RiskPage`, `riesgo/presentacion.js` | Formulario de escenario y resultado |
| Cliente de API | `api/client.js`, `api/conexion.js`, `api/baseUrl.js` | Axios, token en `localStorage`, interceptores 401 |

## 4. Módulos fuera de la aplicación

| Carpeta | Contenido evidenciado |
|---|---|
| `backend/clasificacion/` | Experimentos del clasificador (`hu07_tfidf_preliminar`, `hu07_tfidf_v2`) y de riesgo (`hu08_riesgo`), reglas de etiquetado |
| `backend/evaluation/` | Línea base RAGAS (`ragas_runner.py`, `preflight.py`) |
| `backend/tests/` | 33 archivos de prueba, entre ellos `test_architecture.py` |
| `database/` | `schema.sql` y un modelo de MySQL Workbench (`agro.mwb`, binario, No leído) |
| `knowledge/` | Documentos de conocimiento y sus archivos `.meta.json` |
| `docs/` | `ARQUITECTURA.md`, `INSTALACION.md`, tres documentos HU-08 |
| `auditoria_*`, `piloto_hu07_v2`, `cierre_observaciones_entrenamiento_hu07` | Material del dataset y del entrenamiento (propósito detallado: No leído) |

## 5. Dependencias entre capas

Análisis automático de imports (AST) sobre `backend/app`:

| Capa | Imports externos encontrados |
|---|---|
| `domain` | Solo biblioteca estándar: `abc`, `dataclasses`, `datetime`, `hashlib`, `re`, `uuid` |
| `application` | Solo biblioteca estándar: `dataclasses`, `re`, `unicodedata`, `urllib`, `__future__` |
| `infrastructure` | `fastapi`, `pydantic`, `pydantic_settings`, `sqlalchemy`, `chromadb`, `httpx`, `jwt`, `bcrypt`, `joblib`, `numpy`, entre otros |

- **Violaciones de capa:** ninguna. `domain` no importa `application` ni `infrastructure`, y `application` no importa `infrastructure`.
- **Respaldo en pruebas:** `tests/test_architecture.py` verifica por búsqueda de texto que `domain` y `application` no importen frameworks, y que `bcrypt`, `jwt`, `sqlalchemy` y `httpx` queden dentro de sus adaptadores. Estas pruebas pasaron en la corrida de análisis.

## 6. Código no alcanzable

42 módulos no los importa `app.main` ni ninguna prueba (1 904 líneas, 26 % del código de la aplicación). Son duplicados en inglés de módulos activos:

| Grupo | Módulos |
|---|---|
| Casos de uso | `create_agricultural_context`, `index_knowledge`, `ingest_knowledge`, `list_agricultural_contexts`, `list_knowledge_documents`, `login_farmer`, `register_farmer`, `select_agricultural_context`, `submit_query` |
| Servicios | `document_chunker`, `rag_retrieval_service` |
| Entidades | `agricultural_context`, `evidence`, `farmer`, `knowledge_document`, `query`, `response` |
| Objetos de valor | `content_hash`, `crop`, `password_hash`, `query_text` |
| Puertos de entrada | `index_knowledge_port`, `ingest_knowledge_port`, `login_farmer_port`, `manage_context_port`, `register_farmer_port`, `submit_query_port` |
| Puertos de salida | `agricultural_context_repository_port`, `evidence_repository_port`, `farmer_repository_port`, `knowledge_document_repository_port`, `password_hasher_port`, `query_repository_port` |
| Adaptadores | `template_generation_adapter`, `agricultural_context_repository`, `evidence_repository`, `farmer_repository`, `knowledge_document_repository`, `query_repository`, `bcrypt_password_hasher`, `jwt_token_issuer`, `jwt_token_verifier` |

El análisis no detecta importaciones dinámicas; una búsqueda de `importlib` y `__import__` en `backend/app` no encontró ninguna.

## 7. No evidenciado

- Contenido interno de `FragmentadorDocumentos` y de `referencia_origen.py` (se usan en el flujo, pero no se leyeron en detalle).
- Contenido de `agro.mwb` y de las carpetas de datos del entrenamiento.
- Pruebas del frontend: 4 archivos `*.test.js`; 3 se corrieron con `node --test` (18 pruebas, todas pasaron) y `conexion.test.js` no se corrió.
