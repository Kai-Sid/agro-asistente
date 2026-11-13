# 05 — Plan de remediación OWASP Top 10

| Campo | Valor |
|---|---|
| Proyecto | `Kai-Sid/agro-asistente` |
| Entrada | `docs/04_auditoria_owasp.md` (score 38/100) |
| Rol | Arquitecto de Seguridad |
| Fecha | 2026-11-13 |
| Restricción principal | No romper funcionalidad, no afectar procesos de negocio, mantener compatibilidad hacia atrás |

## Principios de remediación

1. **Compatibilidad primero:** feature flags / variables de entorno con defaults que preserven el comportamiento actual en desarrollo local.
2. **Cambios aditivos:** nuevos roles, logs y límites se agregan sin eliminar endpoints existentes.
3. **Fail-safe progresivo:** en `APP_ENV=production` se endurece; en `development` se advierte sin bloquear el flujo académico.
4. **Validación por capa:** unit + API tests existentes deben seguir en verde; se añaden tests de seguridad sin reescribir casos de negocio.
5. **Rollback simple:** cada mitigación debe revertirse con un flag o revert de commit, sin migración destructiva irreversible en la misma fase.

---

## Estrategia para preservar funcionalidad

| Área de negocio | Cómo se protege durante la remediación |
|---|---|
| Registro / login de agricultores | Misma API y contrato JSON; solo se endurece secreto, rate limit y política de contraseña (gradual). |
| Contextos agrícolas | Sin cambio de modelo de ownership; ya es correcto. |
| Consultas RAG | Prompt hardening y cuotas; mismas rutas `/api/v1/queries`. |
| Conocimiento (ingest/index/list) | Fase 1: flag `KNOWLEDGE_WRITE_ROLE=authenticated` (comportamiento actual). Fase 2: rol `curator` opcional; lecturas siguen disponibles a autenticados. |
| Clima SENAMHI | Auth opcional detrás de flag; default temporal `public` para no romper demos. |
| Clasificación / riesgo | Checksums de modelos; si fallan en dev, warning; en prod, rechazo controlado con 503 ya existente. |
| Frontend | Mantener Bearer en header; migración de storage en fase posterior sin cambiar rutas. |

---

## Roadmap de remediación

```text
Fase 0  (inmediato, ops)     → Secretos y configuración segura
Fase 1  (corto, 1 sprint)    → Auth anti-abuso + logging + surface hardening
Fase 2  (medio, 1–2 sprints) → Control de acceso a knowledge + SSRF/weather
Fase 3  (medio-largo)        → Integridad ML, dependencias, sesión XSS
Fase 4  (continuo)           → Monitoreo, auditoría periódica, score ≥ 70
```

### Orden recomendado

| Orden | ID plan | Hallazgo | Prioridad | Fase |
|---|---|---|---|---|
| 1 | R-01 | Forzar `JWT_SECRET` fuerte / fallar en producción | Crítico* | 0 |
| 2 | R-02 | Logging de seguridad (auth, 401/403, ingest, index) | Alto | 1 |
| 3 | R-03 | Rate limiting en `/auth/login` y `/auth/register` | Alto | 1 |
| 4 | R-04 | Deshabilitar OpenAPI/docs en producción; health mínimo | Alto | 1 |
| 5 | R-05 | Restringir escritura de knowledge (rol/flag) | Alto | 2 |
| 6 | R-06 | Endurecer política de contraseña (compatible) | Alto | 2 |
| 7 | R-07 | Auth opcional + allowlist URL en weather/SSRF | Medio | 2 |
| 8 | R-08 | Mitigación prompt injection / poisoning RAG | Medio | 2–3 |
| 9 | R-09 | Checksum/firma de artefactos `.joblib` | Medio | 3 |
| 10 | R-10 | Pinning + auditoría de dependencias | Medio | 3 |
| 11 | R-11 | Migrar token fuera de `localStorage` (fase segura) | Medio | 3 |
| 12 | R-12 | CORS métodos/headers explícitos | Bajo | 3 |
| 13 | R-13 | Cuotas en queries/RAG y diseño de tenancy futuro | Bajo | 4 |

\*La auditoría no etiquetó “Crítico” a nivel categoría; el plan eleva el secreto JWT a **prioridad crítica operativa** por impacto de compromiso total de sesiones.

---

## Plan por vulnerabilidad

### R-01 — Secreto JWT inseguro por defecto (A02, A05, A07)

| Campo | Detalle |
|---|---|
| **Riesgo** | Tokens falsificables si se despliega con el default `change-me-in-local-env...` |
| **Prioridad** | Crítico |
| **Impacto** | Compromiso de todas las sesiones; elevación a cualquier agricultor |
| **Componentes** | `backend/app/infrastructure/config/settings.py`, `.env.example`, `render.yaml`, arranque `main`/`composition` |
| **Estrategia de mitigación** | (1) En `APP_ENV=production` (o si `PORT` de hosting): **abortar arranque** si `JWT_SECRET` vacío, igual al default, o &lt; 32 chars. (2) En development: log WARNING claro, mantener arranque para no romper labs. (3) Documentar generación (`openssl rand -hex 32`) en `docs/INSTALACION.md` y `.env.example` con placeholder no usable. (4) En Render, exigir env sync de `JWT_SECRET`. |
| **Estrategia de validación** | Test: producción sin secreto → falla al construir settings/container. Test: development con default → arranca + warning. Login/register E2E sin cambio de contrato. |
| **Estrategia de rollback** | Flag `JWT_SECRET_ENFORCE=false` (solo emergencia) o revert del validador; secretos ya rotados permanecen válidos. |

---

### R-02 — Logging y monitoreo de seguridad (A09)

| Campo | Detalle |
|---|---|
| **Riesgo** | Incidentes invisibles (fuerza bruta, ingest malicioso, 401 masivos) |
| **Prioridad** | Alto |
| **Impacto** | Sin detección ni forense; incumplimiento básico de A09 |
| **Componentes** | `auth_controller`, `dependencia_autenticacion`, `knowledge_controller`, nuevo módulo `infrastructure/logging` o config logging estándar |
| **Estrategia de mitigación** | Logger estructurado (JSON o key=value) para: login ok/fail, register, 401, ingest, index, denegación de rol. **No** loguear contraseñas ni JWT completos (solo `sub` truncado). Mantener stdout compatible con Render. Métricas/alertas externas (Sentry) como fase 4 opcional. |
| **Estrategia de validación** | Tests que capturen handlers de logging (`caplog`) en login fallido e ingest. Verificar ausencia de secretos en mensajes. |
| **Estrategia de rollback** | `SECURITY_LOG_LEVEL=WARNING` o desactivar logger de seguridad vía env; API sin cambios. |

---

### R-03 — Rate limiting / anti-abuso en autenticación (A07, A04)

| Campo | Detalle |
|---|---|
| **Riesgo** | Fuerza bruta y registro masivo |
| **Prioridad** | Alto |
| **Impacto** | Toma de cuentas y spam de agricultores |
| **Componentes** | `auth_controller`, middleware o dependencia (p. ej. slowapi / contador en memoria), opcionalmente frontend mensajes 429 |
| **Estrategia de mitigación** | Límite por IP (+ por email en login) p.ej. 10 intentos / 5 min en login y 5 registros / hora. Respuesta `429` con `Retry-After`. Default permisivo en tests (`RATE_LIMIT_ENABLED=false` en pytest). No introducir captcha en esta fase (evitar fricción UX). |
| **Estrategia de validación** | Test de ráfaga → 429; test bajo umbral → 200/201. Suites actuales con flag desactivado. |
| **Estrategia de rollback** | `RATE_LIMIT_ENABLED=false` restaura comportamiento previo. |

---

### R-04 — Hardening de superficie (docs OpenAPI, health) (A05)

| Campo | Detalle |
|---|---|
| **Riesgo** | Reconocimiento de API y disclosure de estado MySQL |
| **Prioridad** | Alto |
| **Impacto** | Facilita ataques dirigidos; información de infraestructura |
| **Componentes** | `main.py` (creación FastAPI), `health_controller.py`, tests que leen `/openapi.json` |
| **Estrategia de mitigación** | Si `APP_ENV=production`: `docs_url=None`, `redoc_url=None`, `openapi_url=None`. Health público: solo `{ "status": "ok" }`; detalle MySQL en `/health/ready` autenticado o solo interno. En development/test: docs y health detallado **siguen** para no romper workflow académico. |
| **Estrategia de validación** | Test matrix por `APP_ENV`. Actualizar tests OpenAPI para marcarlos como solo-dev o setear env development. Smoke `/health` → 200 mínimo. |
| **Estrategia de rollback** | `FORCE_OPENAPI=true` o `APP_ENV=development` en el servicio. |

---

### R-05 — Control de acceso a knowledge (A01, A04, A03)

| Campo | Detalle |
|---|---|
| **Riesgo** | Cualquier usuario autentica y envenena el corpus RAG global |
| **Prioridad** | Alto |
| **Impacto** | Contaminación de respuestas para todos los agricultores |
| **Componentes** | `knowledge_controller`, dominio agricultor / JWT claims, posible columna `rol` o lista env `KNOWLEDGE_CURATOR_EMAILS`, frontend `KnowledgePage` |
| **Estrategia de mitigación** | **Fase A (compatible):** `KNOWLEDGE_MUTATION_POLICY=open` (default actual) vs `curators_only`. En `curators_only`, `POST /ingest` y `POST /index` requieren claim/rol curator; `GET /documents` permanece para autenticados (lectura). **Fase B:** claim `role` en JWT al emitir token; default `farmer`. Sin borrar endpoints. Documentos ya ingeridos no se migran. |
| **Estrategia de validación** | Tests: farmer sin rol → 403 en mutate; curator → 201; list documents sigue 200. UI: ocultar botones de escritura si 403 (degradación graceful). |
| **Estrategia de rollback** | Volver `KNOWLEDGE_MUTATION_POLICY=open`. |

---

### R-06 — Política de contraseña endurecida (A07)

| Campo | Detalle |
|---|---|
| **Riesgo** | Contraseñas débiles facilitan credential stuffing |
| **Prioridad** | Alto |
| **Impacto** | Compromiso de cuentas individuales |
| **Componentes** | `registrar_agricultor.py`, validación frontend `RegisterPage`, mensajes de error API |
| **Estrategia de mitigación** | Mantener mínimo 8; añadir opcional `PASSWORD_POLICY=basic|strong`. `strong`: mayúscula + dígito (sin caracteres especiales obligatorios para no friccionar usuarios rurales). Aplicar **solo a registros nuevos**; hashes existentes intactos. |
| **Estrategia de validación** | Tests de registro con contraseñas que cumplan/fallen. Login de usuarios viejos sin cambio. |
| **Estrategia de rollback** | `PASSWORD_POLICY=basic`. |

---

### R-07 — Weather auth + mitigación SSRF (A01, A10)

| Campo | Detalle |
|---|---|
| **Riesgo** | Proxy público hacia destino configurado; SSRF por env malicioso |
| **Prioridad** | Medio |
| **Impacto** | Abuso de cuota SENAMHI / contacto a hosts internos si se redefine base URL |
| **Componentes** | `weather_controller.py`, `adaptador_senamhi_wis2.py`, settings, futuro embedding HTTP |
| **Estrategia de mitigación** | (1) `WEATHER_REQUIRE_AUTH=false` default (compat); `true` en producción recomendado. (2) Allowlist de hosts para `SENAMHI_WIS2_BASE_URL` y `OLLAMA_BASE_URL` (solo https/http a dominios conocidos / loopback). (3) Rechazar IPs privadas si el esquema se generaliza. (4) Al implementar embeddings externos: misma allowlist. |
| **Estrategia de validación** | Tests con auth on/off; test de URL no permitida → error de configuración al arranque o al primer request. |
| **Estrategia de rollback** | Flags a `false` / vaciar allowlist enforcement. |

---

### R-08 — Prompt injection / envenenamiento RAG (A03, A04)

| Campo | Detalle |
|---|---|
| **Riesgo** | Instrucciones maliciosas en consulta o documentos alteran la respuesta |
| **Prioridad** | Medio |
| **Impacto** | Consejos agrícolas incorrectos; pérdida de confianza |
| **Componentes** | `adaptador_generacion_ollama.py`, ingest knowledge, `suficiencia_contexto` |
| **Estrategia de mitigación** | Separar claramente system vs user; delimitar fragmentos con marcadores; rechazar/escapar patrones obvios de “ignora instrucciones” en ingest (lista conservadora); mantener `texto_con_cantidades_controladas`. No cambiar el contrato de `/queries`. Acoplar a R-05 para reducir writers. |
| **Estrategia de validación** | Casos de prueba con prompts adversariales; assert de que la system prompt sigue vigente y no se filtran secretos. Regresión RAGAS/baseline si aplica. |
| **Estrategia de rollback** | Flag `PROMPT_HARDENING=false` vuelve al armado actual del prompt. |

---

### R-09 — Integridad de modelos joblib (A08, A06)

| Campo | Detalle |
|---|---|
| **Riesgo** | Sustitución de `.joblib` → RCE / predicciones manipuladas |
| **Prioridad** | Medio |
| **Impacto** | Ejecución de código o sesgo del clasificador/riesgo |
| **Componentes** | `adaptador_clasificador_tfidf.py`, `adaptador_predictor_riesgo.py`, manifiestos de experimentos, CI |
| **Estrategia de mitigación** | Archivo `modelos.sha256` (o campo en manifiesto existente) verificado antes de `joblib.load`. En development: warning si mismatch. En production: no cargar → 503 ya contemplado (`ErrorClasificadorNoDisponible` / predictor). No cambiar algoritmo ML. |
| **Estrategia de validación** | Test con hash correcto/incorrecto. Inferencia existente con artefactos del repo. |
| **Estrategia de rollback** | `MODEL_INTEGRITY_CHECK=false`. |

---

### R-10 — Gestión de componentes vulnerables (A06)

| Campo | Detalle |
|---|---|
| **Riesgo** | CVEs en stack FastAPI/Chroma/RAGAS/npm |
| **Prioridad** | Medio |
| **Impacto** | Explotación vía dependencia transitiva |
| **Componentes** | `backend/requirements.txt`, `frontend/package-lock.json`, CI |
| **Estrategia de mitigación** | Generar `requirements.lock` o pin de versiones de runtime; job CI `pip-audit` + `npm audit --omit=dev`; Dependabot/Renovate. Separar deps de evaluación RAGAS del runtime de API si es viable sin romper `evaluation/`. |
| **Estrategia de validación** | Pipeline verde; instalar desde lock en entorno limpio; smoke API. |
| **Estrategia de rollback** | Volver al `requirements.txt` por rangos; freeze anterior del lock. |

---

### R-11 — Almacenamiento de sesión (XSS → robo de JWT) (A02, A07)

| Campo | Detalle |
|---|---|
| **Riesgo** | XSS en frontend roba `localStorage` token |
| **Prioridad** | Medio |
| **Impacto** | Secuestro de sesión |
| **Componentes** | `frontend/src/api/client.js`, posible cookie HttpOnly en backend, CORS credentials |
| **Estrategia de mitigación** | **No migrar de golpe.** Fase 1: headers CSP básicos en static hosting + sanitización UI. Fase 2 (opcional): cookie `HttpOnly` + `Secure` + `SameSite` con endpoint refresh; dual-read temporal (cookie o Bearer) para no romper clientes. Mantener paths de API. |
| **Estrategia de validación** | Login → acceso a rutas protegidas; logout limpia sesión; tests e2e manuales en Pages + API. |
| **Estrategia de rollback** | Feature flag `AUTH_STORAGE=localstorage` (default actual). |

---

### R-12 — CORS explícito (A05)

| Campo | Detalle |
|---|---|
| **Riesgo** | Superficie de métodos/headers demasiado amplia con credentials |
| **Prioridad** | Bajo |
| **Impacto** | Bajo-medio si hay XSS o orígenes mal configurados |
| **Componentes** | `cors.py`, frontend axios |
| **Estrategia de mitigación** | Permitir solo `GET, POST, OPTIONS` y headers `Authorization, Content-Type, Accept`. Verificar preflight del front actual. |
| **Estrategia de validación** | Suite `test_cors.py` ampliada; smoke UI login + query. |
| **Estrategia de rollback** | Restaurar `allow_methods=["*"]` / `allow_headers=["*"]`. |

---

### R-13 — Cuotas RAG y tenancy futuro (A04)

| Campo | Detalle |
|---|---|
| **Riesgo** | Abuso de coste/latencia Ollama; conocimiento global sin partición |
| **Prioridad** | Bajo (diseño evolutivo) |
| **Impacto** | Degradación del servicio; deuda de multi-tenant |
| **Componentes** | `query_controller`, Ollama adapter, modelo de documentos |
| **Estrategia de mitigación** | Rate limit suave en `/queries` y `/riesgo`. Documento de diseño para tenancy por `agricultor_id` o “organizaciones” en PMV2 — **sin migrar datos en PMV1**. |
| **Estrategia de validación** | Pruebas de cuota; ADR en `docs/`. |
| **Estrategia de rollback** | Desactivar cuotas por env; ADR no afecta runtime. |

---

## Riesgos de implementación

| Riesgo | Probabilidad | Mitigación |
|---|---|---|
| Arranque en prod falla por `JWT_SECRET` ausente | Alta al activar R-01 | Checklist pre-deploy; secret en Render antes del release |
| Tests OpenAPI fallan tras R-04 | Alta | Ejecutar tests con `APP_ENV=development` |
| 403 en knowledge rompe demo en clase | Media | Default `KNOWLEDGE_MUTATION_POLICY=open` hasta demo; activar curators solo en prod |
| Rate limit en CI/pytest flaky | Media | Deshabilitar por env en `conftest.py` |
| Cookie auth rompe CORS Pages↔API | Media | Dual mode; probar `SameSite=None; Secure` solo si hace falta cross-site |
| Checksum de modelos desactualizado tras reentrenar | Media | Script de regeneración de hashes en carpeta de experimentos |
| Pinning de deps rompe Python 3.13 / RAGAS | Media | Lock separado runtime vs evaluation |

---

## Hitos y criterios de aceptación globales

| Hito | Criterio | Score objetivo (orientativo) |
|---|---|---|
| Tras Fase 0–1 | Secreto enforced en prod; logs de auth; rate limit; docs off en prod | ≥ 50 |
| Tras Fase 2 | Knowledge mutate restringible; weather/SSRF endurecidos; password policy | ≥ 60 |
| Tras Fase 3 | Integridad modelos; deps auditadas; CORS estricto; plan sesión | ≥ 70 |
| Continuo | Alertas básicas + revisión trimestral OWASP | Mantener ≥ 70 |

### Definition of Done por cambio

- Tests previos de negocio en verde.
- Nuevo test de seguridad asociado al hallazgo.
- Flag/env documentado en `.env.example` e `INSTALACION.md`.
- Rollback descrito y probado (al menos en local).
- Sin cambio de contrato JSON salvo códigos nuevos esperados (`403`, `429`) documentados.

---

## Matriz resumen

| ID | Categorías OWASP | Prioridad | Fase | Compatibilidad |
|---|---|---|---|---|
| R-01 | A02, A05, A07 | Crítico | 0 | Dev sigue; prod enforce |
| R-02 | A09 | Alto | 1 | Solo aditivo |
| R-03 | A07, A04 | Alto | 1 | Flag off en tests |
| R-04 | A05 | Alto | 1 | Docs en development |
| R-05 | A01, A04, A03 | Alto | 2 | Policy `open` default |
| R-06 | A07 | Alto | 2 | Solo registros nuevos |
| R-07 | A01, A10 | Medio | 2 | Auth weather opcional |
| R-08 | A03, A04 | Medio | 2–3 | Flag hardening |
| R-09 | A08, A06 | Medio | 3 | Warning en dev |
| R-10 | A06 | Medio | 3 | Lock reversible |
| R-11 | A02, A07 | Medio | 3 | Dual storage |
| R-12 | A05 | Bajo | 3 | Lista explícita |
| R-13 | A04 | Bajo | 4 | Diseño / cuotas suaves |

---

## Conclusión

El plan prioriza **controles operativos de alto impacto y bajo riesgo de regresión** (secreto JWT, logging, rate limit, cierre de docs) antes de cambios de autorización sobre knowledge y endurecimientos de integridad/ML. Todas las mitigaciones se diseñan con **feature flags y defaults compatibles** para no interrumpir el flujo académico ni los procesos de negocio del PMV1. La implementación concreta queda fuera del alcance de este documento (siguiente agente: ejecutor/remediador).
