# Inventario funcional y endpoints detectados (Fase 4, Prompt 7)

## Alcance y método

- **Fuentes:** `evidencias/ejecucion/openapi.json` (contrato de la API del backend en ejecución), rutas de `frontend/src/App.jsx` y nombres de archivos de `frontend/src/` (pages, components, consulta, riesgo).
- **Regla:** solo se registra lo que consta en esas fuentes. Lo demás figura como «No evidenciado» o «No ejecutado».
- **Limitación importante:** el backend corrió sin base de datos (`mysql: disconnected`). Por eso solo se pudo ejecutar `/health`, los endpoints que no usan la base y el rechazo 401 de los protegidos. Todo flujo que requiere sesión o base de datos se describe desde el contrato, no desde una ejecución.
- **Pantallas:** se leyeron el menú (`AppHeader.jsx`), las rutas (`App.jsx`), la protección de rutas y el manejo de errores del login. El resto del contenido de las pantallas no se leyó, y en ejecución solo se vio la pantalla de login. Los campos de los formularios salen de los esquemas de la API.

## 1. Módulos funcionales

| Módulo | Evidencia | Estado de verificación |
|---|---|---|
| Autenticación de agricultores (registro, inicio de sesión) | `POST /api/v1/auth/register`, `POST /api/v1/auth/login`; `RegisterPage.jsx`, `LoginPage.jsx` | Ejecutado: ambos responden 500 sin base de datos |
| Contextos agrícolas (parcela, cultivo, región) | `GET/POST /api/v1/contexts`, `POST /api/v1/contexts/{context_id}/select`; `ContextPage.jsx` | Solo se verificó el 401 sin sesión en `GET /contexts` |
| Consulta en lenguaje natural con evidencias | `POST /api/v1/queries`; `QueryPage.jsx` | No ejecutado |
| Gestión de conocimiento (ingesta, indexación, listado) | `POST /api/v1/knowledge/ingest`, `POST /api/v1/knowledge/index`, `GET /api/v1/knowledge/documents`; `KnowledgePage.jsx` | Solo se verificó el 401 sin sesión en el listado |
| Clasificación de consultas | `POST /api/v1/clasificacion` | No ejecutado |
| Predicción de riesgo | `POST /api/v1/riesgo`; `RiskPage.jsx` | No ejecutado |
| Observaciones meteorológicas | `GET /api/v1/weather/observations` | Ejecutado: 200 sin sesión |
| Salud del servicio | `GET /health` | Ejecutado: 200 con `mysql: disconnected` |
| Panel principal | `DashboardPage.jsx`, ruta `/dashboard` | No evidenciado qué endpoint usa |

## 2. Menús y navegación

Rutas del frontend (`frontend/src/App.jsx:15-23`):

| Ruta | Pantalla | Observación |
|---|---|---|
| `/` | `HomePage` | Inicio público |
| `/register` | `RegisterPage` | Registro |
| `/login` | `LoginPage` | Verificada en ejecución (captura del login) |
| `/dashboard` | `DashboardPage` | |
| `/context` | `ContextPage` | |
| `/query` | `QueryPage` | |
| `/knowledge` | `KnowledgePage` | |
| `/riesgo` | `RiskPage` | La ruta está en español y las demás en inglés |

- Existen `PublicShell`, `AuthenticatedShell`, `ProtectedRoute`, `PublicHeader`, `AppHeader`, `AuthFooter` y `BrandMark` en `frontend/src/components/`.
- Las rutas `/dashboard`, `/context`, `/query`, `/knowledge` y `/riesgo` están dentro de `ProtectedRoute` (`App.jsx:18`). Ese componente solo comprueba que exista un token en `localStorage`; la validez la decide el servidor, y un 401 limpia la sesión.
- Menú de la zona autenticada (`AppHeader.jsx`): Dashboard, Contexto, Consulta, Base de conocimiento, Riesgo experimental y Cerrar sesión.

## 3. Formularios

Los campos salen de los esquemas de la API. Su correspondencia exacta con lo que muestra cada pantalla no se verificó, salvo en el login.

| Formulario | Campos (obligatorios en negrita) | Evidencia |
|---|---|---|
| Registro | **names**, **last_names**, **email**, **password** | `RegisterFarmerRequest` |
| Inicio de sesión | **email**, **password** | `LoginFarmerRequest`; captura del login (Correo, Contraseña, botón «Iniciar sesión», enlaces «Crear cuenta» y «Volver al inicio») |
| Crear contexto agrícola | plot_name, **crop**, **region**, notes | `CreateContextRequest` |
| Consulta | **text** | `SubmitQueryRequest` |
| Ingesta de conocimiento | **title**, **topic**, **content** | `IngestKnowledgeRequest` |
| Clasificación de consulta | **text** | `ClasificacionRequest` |
| Escenario de riesgo | **familia_escenario**, **cultivo**, **region**, **etapa_fenologica**, temperatura_c, precipitacion_mm, **dias_sin_lluvia**, **sintoma_observado**, **proporcion_afectada**, **condicion_suelo** | `EscenarioRiesgoRequest` |

## 4. APIs expuestas por el backend

La columna «Sesión» indica si el contrato declara seguridad (`security`) para ese endpoint.

| Método y ruta | Sesión | Entrada | Respuestas declaradas | Verificado en ejecución |
|---|---|---|---|---|
| `GET /health` | No | — | 200 | 200, con `mysql: disconnected` |
| `POST /api/v1/auth/register` | No | `RegisterFarmerRequest` | 201, 422 | 500 |
| `POST /api/v1/auth/login` | No | `LoginFarmerRequest` | 200, 422 | 500 (3 de 3 intentos) |
| `GET /api/v1/contexts` | Sí | — | 200 | 401 sin sesión |
| `POST /api/v1/contexts` | Sí | `CreateContextRequest` | 201, 422 | No ejecutado |
| `POST /api/v1/contexts/{context_id}/select` | Sí | parámetro de ruta `context_id` | 200, 422 | No ejecutado |
| `POST /api/v1/queries` | Sí | `SubmitQueryRequest` | 201, 422 | No ejecutado |
| `POST /api/v1/knowledge/ingest` | Sí | `IngestKnowledgeRequest` | 201, 422 | No ejecutado |
| `POST /api/v1/knowledge/index` | Sí | — | 200 | No ejecutado |
| `GET /api/v1/knowledge/documents` | Sí | — | 200 | 401 sin sesión |
| `GET /api/v1/weather/observations` | No | parámetros: limit, datetime, bbox, wigos_station_identifier, name, sortby | 200, 422 | 200 sin sesión |
| `POST /api/v1/clasificacion` | Sí | `ClasificacionRequest` | 200, 422 | No ejecutado |
| `POST /api/v1/riesgo` | Sí | `EscenarioRiesgoRequest` | 200, 422 | No ejecutado |

Total: 13 endpoints (4 públicos y 9 con sesión según el contrato).

### Datos que devuelven los endpoints principales

| Respuesta | Campos |
|---|---|
| `LoginFarmerResponse` | access_token, token_type, farmer |
| `SubmitQueryResponse` | id, text, answer, generation_method, created_at, context, evidences, classification |
| `QueryEvidenceResponse` | document_id, document_title, chunk_id, excerpt, similarity_score, rank_order, origin_reference (opcional) |
| `QueryClassificationResponse` | category, abstained, reason, margin, top_class, top_score, second_class, second_score, scores_are_calibrated, available, error |
| `ClasificacionResponse` | categoria, abstencion, motivo_abstencion, clase_primera, puntuacion_primera, clase_segunda, puntuacion_segunda, margen, puntuaciones_calibradas |
| `PrediccionRiesgoResponse` | categoria_predicha, identificador_modelo, version_reglas, naturaleza, es_riesgo_agricola_validado |
| `IndexKnowledgeResponse` | indexed_documents, total_chunks, collection, documents |
| `KnowledgeDocumentResponse` | id, title, topic, source_path, content_hash, chunk_count, ingested_at, status |
| `AgriculturalContextResponse` | id, farmer_id, plot_name, crop, region, notes, is_selected, created_at |
| `WeatherObservationResponse` | station_id, station_name, latitude, longitude, altitude, observation_datetime, air_temperature, dewpoint_temperature, precipitation |

## 5. APIs y servicios consumidos

Según `evidencias/configuracion/servicios.md`:

| Servicio | Tipo | Uso evidenciado |
|---|---|---|
| SENAMHI WIS 2.0 (OGC API) | API externa remota | Fuente de las observaciones meteorológicas |
| Ollama | Servidor de modelo de lenguaje local | Generación de respuestas |
| Chroma | Almacén vectorial local | Indexación y recuperación del conocimiento |
| MySQL | Base de datos | Persistencia; no estuvo disponible en la ejecución |
| Backend desde el frontend | Proxy de Vite (`/health` y `/api`) | El frontend consume el backend |

## 6. Flujos principales (inferidos del contrato)

Ningún flujo se ejecutó de punta a punta, porque el backend no tuvo base de datos.

1. **Acceso:** registro (`register`) → inicio de sesión (`login`, devuelve `access_token`) → uso de los endpoints protegidos.
2. **Contexto agrícola:** crear contexto → seleccionarlo → consultar. La consulta exige un contexto seleccionado: sin él, el backend responde 409. La respuesta incluye un campo `context`.
3. **Consulta:** enviar `text` → el backend responde con `answer`, `generation_method`, `evidences` y `classification`.
4. **Conocimiento:** ingerir documento → indexar → listar documentos.
5. **Clasificación y riesgo:** `clasificacion` recibe un texto y puede abstenerse; `riesgo` recibe un escenario y devuelve una categoría con campos de identificación del modelo y de validación.
6. **Clima:** consulta pública de observaciones con filtros.

## 7. Candidatos a hallazgo para el Prompt 11

| ID | Hallazgo | Evidencia | Severidad propuesta |
|---|---|---|---|
| C-01 | `POST /knowledge/ingest` y `POST /knowledge/index` solo exigen sesión; el controlador recibe el id del agricultor y no lo usa, y la pantalla «Base de conocimiento» está en el menú de todo usuario. No hay roles. | `knowledge_controller.py`; `AppHeader.jsx` | Medio |
| C-02 | Contrato incompleto: login declara solo 200 y 422, y los endpoints protegidos declaran solo 200 o 201 y 422. Se observó 401 en ejecución y 500 en login y registro. | `openapi.json`; `backend_logs.txt:8-9`, `:13` | Medio |
| C-03 | Mezcla de inglés y español en rutas, campos y esquemas (`/contexts`, `/queries` vs `/clasificacion`, `/riesgo`; `category` vs `categoria`). | `openapi.json`; `App.jsx:23` | Bajo |
| C-04 | Existen dos esquemas de clasificación en idiomas distintos: `QueryClassificationResponse` y `ClasificacionResponse`. | `openapi.json` | Bajo |
| C-05 | `GET /weather/observations` es público y reenvía filtros a una API externa. Si es intencional: **No evidenciado**. | `openapi.json`; `backend_logs.txt:10` | Medio |

## 8. No evidenciado

- Contenido y campos reales de las pantallas, salvo el login.
- Comportamiento de cualquier endpoint que requiera sesión o base de datos.
- Roles o permisos de usuario.
