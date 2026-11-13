# 04 — Auditoría OWASP Top 10

| Campo | Valor |
|---|---|
| Proyecto | `Kai-Sid/agro-asistente` |
| Alcance | Frontend React/Vite, backend FastAPI hexagonal, MySQL, Chroma, Ollama, SENAMHI WIS2, despliegue `render.yaml` |
| Commit analizado | `eaac3da` (rama `main`) |
| Metodología | OWASP Top 10 (2021) — revisión estática del repositorio |
| Restricciones | Solo evaluación; sin correcciones ni cambios de código |
| Fecha | 2026-11-13 |
| Auditor | Agente Auditor OWASP Top 10 |

## Resumen ejecutivo

El PMV1 aplica controles básicos útiles (JWT Bearer, bcrypt, SQLAlchemy ORM, aislamiento de contextos por agricultor, CORS con lista/regex acotada). Persisten riesgos relevantes de diseño y operación: secreto JWT por defecto, conocimiento compartido sin roles, endpoint meteorológico público, ausencia de logging/rate limiting, exposición de OpenAPI y carga de modelos `joblib` sin verificación de integridad.

**Score global de seguridad: 38 / 100**  
**Nivel: Débil (riesgo alto para un entorno expuesto a Internet)**

| Severidad | Cantidad de categorías |
|---|---|
| Crítico | 0 |
| Alto | 6 |
| Medio | 3 |
| Bajo | 1 |

---

## A01 — Broken Access Control

| Campo | Valor |
|---|---|
| **Estado** | Deficiente con controles parciales |
| **Severidad** | Alto |
| **Impacto** | Alto — un agricultor autenticado puede ingerir/indexar/listar toda la base de conocimiento compartida e influir en respuestas RAG de otros usuarios |
| **Probabilidad** | Alta — basta registrarse y llamar a `/api/v1/knowledge/*` |

### Evidencia

- Contextos sí están acotados por `agricultor_id` del JWT (`context_controller.py`, `seleccionar_para_agricultor` filtra por dueño).
- Conocimiento: cualquier agricultor autenticado puede `POST /ingest`, `POST /index` y `GET /documents`; no hay rol admin ni tenancy (`knowledge_controller.py`).
- `listar_todos()` en el repositorio de documentos no filtra por propietario.
- `GET /api/v1/weather/observations` es público (sin `Depends` de autenticación).
- `/health` expone estado de MySQL sin autenticación.

### Nota positiva

Pruebas de no-selección de contexto ajeno (`test_cannot_select_another_farmer_context`, `test_submit_query_does_not_use_another_farmer_context`) refuerzan el control de isolation en contextos/consultas.

---

## A02 — Cryptographic Failures

| Campo | Valor |
|---|---|
| **Estado** | Parcialmente controlado; fallo crítico de configuración por defecto |
| **Severidad** | Alto |
| **Impacto** | Alto — compromiso de sesiones si el secreto JWT es predecible o no se rota |
| **Probabilidad** | Media-Alta en despliegues que olviden `JWT_SECRET` |

### Evidencia

- Hash de contraseñas con **bcrypt** (`hasher_contrasena_bcrypt.py`) — adecuado.
- JWT HS256 con `exp` (`emisor_token_jwt.py`, `verificador_token_jwt.py`).
- Secreto por defecto en código: `jwt_secret: str = "change-me-in-local-env-do-not-use-in-production"` (`settings.py`).
- `.env.example` deja `JWT_SECRET=` vacío; sin override se usa el default inseguro.
- Token de acceso guardado en `localStorage` (`frontend/src/api/client.js`) — expuesto a XSS.
- No hay cifrado en tránsito definido en la app (depende del hosting); no hay force HTTPS en FastAPI.
- Contraseñas no viajan en claro en persistencia (solo hash en `agricultores.contrasena_hash`).

---

## A03 — Injection

| Campo | Valor |
|---|---|
| **Estado** | SQL/ORM bajo riesgo; inyección a LLM/RAG residual |
| **Severidad** | Medio |
| **Impacto** | Medio-Alto sobre integridad de respuestas y posible abuso del modelo |
| **Probabilidad** | Media — el texto del usuario y documentos ingeridos entran al prompt |

### Evidencia

- Persistencia vía SQLAlchemy ORM / parámetros enlazados; `text("SELECT 1")` solo en health ping — riesgo SQL injection bajo.
- Validación de entrada con Pydantic (`Field`, enums de riesgo, longitudes en consultas/conocimiento).
- Consultas y documentos se interpolan en el prompt de Ollama (`construir_prompt_agricola` en `adaptador_generacion_ollama.py`) → **prompt injection / poisoning** del RAG.
- Ingestión de conocimiento por cualquier usuario autenticado amplifica inyección de contenido malicioso en la base vectorial.
- No se observó `eval`, `exec`, `os.system` ni concatenación SQL con input de usuario en la capa de aplicación.

---

## A04 — Insecure Design

| Campo | Valor |
|---|---|
| **Estado** | Diseño funcional de PMV1 sin modelo de amenazas maduro |
| **Severidad** | Alto |
| **Impacto** | Alto — abuso de registro abierto, contaminación del conocimiento y sesiones largas |
| **Probabilidad** | Alta en despliegue público |

### Evidencia

- Registro abierto sin verificación de correo (`POST /api/v1/auth/register`).
- Un solo tipo de actor (agricultor); sin RBAC para operaciones privilegiadas (conocimiento, indexación).
- Base de conocimiento **global** compartida entre todos los agricultores.
- JWT de 120 minutos sin refresh, sin denylist/revocación (`JWT_EXPIRE_MINUTES=120`).
- Sin rate limiting, captcha ni anti-abuso en auth o APIs costosas (RAG/Ollama).
- `render.yaml` documenta plan free y secretos sync:false, pero no define controles de amenaza (WAF, disco persistente Chroma, aislamiento Ollama).

---

## A05 — Security Misconfiguration

| Campo | Valor |
|---|---|
| **Estado** | Varias exposiciones por defecto de framework/despliegue |
| **Severidad** | Alto |
| **Impacto** | Medio-Alto — reconocimiento y abuso de superficie de ataque |
| **Probabilidad** | Alta |

### Evidencia

- FastAPI deja habilitados `/docs`, `/redoc` y `/openapi.json` por defecto (confirmado por tests que consumen OpenAPI).
- CORS: orígenes acotados + regex Pages (bien); pero `allow_methods=["*"]` y `allow_headers=["*"]` con `allow_credentials=True` (`cors.py`).
- Health disclosure: `mysql: connected|disconnected` (`health_controller.py`).
- Escucha en `0.0.0.0` en arranque de producción (`main.py`).
- Secretos bien excluidos en `.gitignore` (`.env`, `*.pem`) — control positivo.
- `render.yaml` no fija `JWT_SECRET` ni `APP_ENV=production` de forma segura por defecto (sync:false, responsabilidad del operador).

---

## A06 — Vulnerable and Outdated Components

| Campo | Valor |
|---|---|
| **Estado** | Dependencias amplias sin evidencia de gestión continua de CVEs |
| **Severidad** | Medio |
| **Impacto** | Medio — cadena de suministro (Chroma, RAGAS/LangChain, scikit-learn) |
| **Probabilidad** | Media |

### Evidencia

- `backend/requirements.txt` usa rangos abiertos (`fastapi>=0.115.0`, `chromadb>=0.5.23`, etc.) sin pin estricto ni archivo de lock Python.
- Frontend sí tiene `package-lock.json` (axios, React 18, Vite 5.4.11).
- No hay Dependabot, `npm audit`/`pip-audit` ni SBOM en el repositorio.
- Artefactos ML embebidos (`.joblib`) aumentan superficie y acoplamiento a versiones de scikit-learn/joblib.
- Stack RAGAS 0.4.3 + langchain (evaluación) amplía el árbol de dependencias aunque esté fuera del dominio de negocio.

---

## A07 — Identification and Authentication Failures

| Campo | Valor |
|---|---|
| **Estado** | Autenticación básica presente; controles anti-abuso ausentes |
| **Severidad** | Alto |
| **Impacto** | Alto — toma de cuentas / fuerza bruta / sesiones robadas |
| **Probabilidad** | Media-Alta |

### Evidencia

- Login emite Bearer JWT; dependencia HTTPBearer valida token (`dependencia_autenticacion.py`).
- Política de contraseña: solo longitud ≥ 8, sin complejidad ni denylist (`registrar_agricultor.py`).
- Sin rate limit, lockout ni MFA.
- Mensaje genérico de credenciales inválidas en login (positivo frente a enumeración excesiva; el registro sí distingue correo duplicado 409).
- Sesión solo en `localStorage`; `ProtectedRoute` comprueba presencia del token, no su validez criptográfica en cliente.
- Sin invalidación de tokens tras cambio de contraseña (no existe flujo de cambio).
- Riesgo agravado por secreto JWT por defecto (A02).

---

## A08 — Software and Data Integrity Failures

| Campo | Valor |
|---|---|
| **Estado** | Integridad de artefactos ML y conocimiento no verificada |
| **Severidad** | Medio |
| **Impacto** | Alto si se sustituye un modelo o se envenena el corpus |
| **Probabilidad** | Media |

### Evidencia

- Clasificador y predictor cargan modelos con `joblib.load` sin firma, checksum ni allowlist criptográfica (`adaptador_clasificador_tfidf.py`, `adaptador_predictor_riesgo.py`). `joblib`/`pickle` ejecutan objetos arbitrarios si el archivo se altera.
- Ingestión autenticada escribe archivos en `knowledge/` e indexa en Chroma sin workflow de revisión/aprobación.
- No hay verificación de integridad de builds CI/CD ni firmas de release en el repo.
- Positivo: lockfile npm; secretos no commiteados; blueprint Render evita secretos en YAML.

---

## A09 — Security Logging and Monitoring Failures

| Campo | Valor |
|---|---|
| **Estado** | Ausencia casi total de telemetría de seguridad |
| **Severidad** | Alto |
| **Impacto** | Alto — incidentes no detectables ni auditables |
| **Probabilidad** | Alta (falla garantizada de detección) |

### Evidencia

- No hay configuración de `logging` de seguridad en `backend/app` (sin logger de auth fallido, ingest, index, ni accesos denegados).
- No hay integración con SIEM/APM (Sentry, métricas Prometheus, alertas).
- Health check no sustituye auditoría: solo reporta conectividad MySQL.
- Acciones sensibles (registro, login fallido, ingest de conocimiento, indexación) no dejan traza estructurada en código de aplicación.

---

## A10 — Server-Side Request Forgery (SSRF)

| Campo | Valor |
|---|---|
| **Estado** | Riesgo residual por URLs de infraestructura configurables; no hay SSRF clásico dirigido por URL de usuario |
| **Severidad** | Bajo |
| **Impacto** | Medio si `SENAMHI_WIS2_BASE_URL` / `OLLAMA_BASE_URL` apuntan a red interna |
| **Probabilidad** | Baja-Media (requiere mal configuración o compromiso de env) |

### Evidencia

- Cliente SENAMHI construye URL fija desde settings + path de colección; parámetros de query (`bbox`, `datetime`, etc.) sí son controlados por el cliente HTTP público (`weather_controller.py` + `adaptador_senamhi_wis2.py`).
- El usuario **no** elige la URL base; mitiga SSRF directo tipo “fetch esta URL”.
- `OLLAMA_BASE_URL` y futuro `EMBEDDING_API_URL` son server-side; un valor malicioso en entorno haría que el backend contacte hosts internos.
- Endpoint weather sin autenticación amplifica el abuso como proxy hacia el destino configurado.
- `ExternalEmbeddingAdapter` aún no realiza llamadas HTTP (proveedor pendiente) — riesgo futuro si se implementa sin allowlist.

---

## Matriz consolidada

| ID | Categoría | Severidad | Score parcial (0–10) |
|---|---|---|---|
| A01 | Broken Access Control | Alto | 3 |
| A02 | Cryptographic Failures | Alto | 3 |
| A03 | Injection | Medio | 5 |
| A04 | Insecure Design | Alto | 3 |
| A05 | Security Misconfiguration | Alto | 3 |
| A06 | Vulnerable Components | Medio | 5 |
| A07 | Authentication Failures | Alto | 3 |
| A08 | Software and Data Integrity Failures | Medio | 5 |
| A09 | Logging and Monitoring Failures | Alto | 2 |
| A10 | SSRF | Bajo | 7 |
| | **Score global** | | **38 / 100** |

Cálculo: promedio de scores parciales × 10.

---

## Controles observados (fortalezas)

1. Arquitectura hexagonal con puertos de seguridad (hasher, emisor/verificador JWT).
2. bcrypt para contraseñas; JWT con expiración.
3. Ownership de contextos agrícolas validado en repositorio y cubierto por tests.
4. ORM SQLAlchemy reduce inyección SQL.
5. CORS con denegación de `*` literal y regex restringida a subdominios Pages HTTPS.
6. `.gitignore` excluye `.env` y material sensible.
7. Blueprint Render marca secretos como `sync: false` (no hardcodeados en YAML).

---

## Hallazgos prioritarios (solo diagnóstico)

| Prioridad | Hallazgo | Categorías |
|---|---|---|
| P1 | Secreto JWT por defecto / vacío en ejemplo de entorno | A02, A05, A07 |
| P1 | Knowledge compartido sin roles (ingest/index/list) | A01, A04, A03 |
| P1 | Sin logging ni monitoreo de seguridad | A09 |
| P2 | Sin rate limiting / lockout en autenticación | A07, A04 |
| P2 | OpenAPI/docs y health con disclosure | A05 |
| P2 | Token en `localStorage` + XSS implícito | A02, A07 |
| P3 | `joblib.load` sin verificación de integridad | A08, A06 |
| P3 | Weather público + URL base configurable | A01, A10 |

---

## Conclusión

El proyecto demuestra conciencia básica de autenticación y aislamiento de datos de contexto, coherente con un PMV académico. Para un despliegue real, el nivel actual (**38/100**) no es aceptable: dominan fallos de autorización sobre el corpus RAG, configuración criptográfica frágil, ausencia de observabilidad y falta de controles anti-abuso. Esta auditoría no propone ni implementa remediaciones, conforme al mandato del auditor.
