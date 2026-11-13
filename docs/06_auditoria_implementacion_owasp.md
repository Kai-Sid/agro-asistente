# 06 — Auditoría de implementación OWASP Top 10

| Campo | Valor |
|---|---|
| Proyecto | `Kai-Sid/agro-asistente` |
| Rol | Auditor Independiente de Seguridad |
| Entradas | `docs/04_auditoria_owasp.md`, `docs/05_plan_owasp.md`, estado actual del código |
| Fecha | 2026-11-13 |
| Método | Revisión estática de remediaciones + ejecución selectiva de `tests/test_security_owasp.py` |
| Restricción | No se asume corrección sin evidencia |

## Resumen ejecutivo

Las remediaciones del plan **están presentes en código** de forma mayormente aditiva y con feature flags. Varios controles críticos **no quedan activos con los defaults de desarrollo/demo** (`KNOWLEDGE_MUTATION_POLICY=open`, `PASSWORD_POLICY=basic`, `WEATHER_REQUIRE_AUTH=false`, allowlist/JWT enforce solo en `APP_ENV=production`). Por tanto, el riesgo residual depende fuertemente de la configuración de despliegue.

| Score auditoría inicial (04) | **38 / 100** |
| Score tras implementación (06) | **60 / 100** |
| Variación | **+22** |
| Nivel actual | **Aceptable con reservas** (mejoría clara; aún insuficiente para producción sin activar flags endurecidos) |

| Estado | Cantidad (categorías OWASP) |
|---|---|
| Corregida | 1 |
| Parcialmente corregida | 8 |
| No corregida | 1 |

---

## Evidencia de verificación automatizada

Ejecutado en este entorno:

```text
pytest tests/test_security_owasp.py -k "not login_y_sesion and not api_con_token and not roles_knowledge"
→ 11 passed
```

Casos que **no pudieron validarse aquí** por ausencia de MySQL (`OperationalError 2003` a `localhost`):

- `test_login_y_sesion_jwt_incluye_role_y_exp`
- `test_api_con_token_permite_gestion_de_contexto`
- `test_roles_knowledge_curators_only_bloquea_farmer`

La lógica de esos casos **existe en el código y en el test**; la no ejecución no implica ausencia del control, pero **sí limita la evidencia dinámica** de login/roles/API con persistencia en esta corrida.

---

## Veredicto por categoría OWASP

### A01 — Broken Access Control

| Campo | Valor |
|---|---|
| **Estado** | Parcialmente corregida |
| **Plan** | R-05, R-07 |
| **Severidad residual** | Medio-Alto (si se dejan defaults) |

**Evidencias de remediación**

- `dependencia_escritura_conocimiento` exige rol `curator` cuando `KNOWLEDGE_MUTATION_POLICY=curators_only` (`dependencia_autenticacion.py`).
- JWT incluye `role`; login responde `farmer.role` (`emisor_token_jwt.py`, `auth_controller.py`, `iniciar_sesion_agricultor.py`).
- `WEATHER_REQUIRE_AUTH` puede exigir Bearer en weather (`weather_controller.py`).

**Evidencias de que NO está plenamente corregida**

- Default `knowledge_mutation_policy: str = "open"` → cualquier autenticado sigue pudiendo ingerir/indexar.
- Default `weather_require_auth: bool = False` → endpoint meteorológico sigue público.
- Ownership de contextos ya era correcto antes; no es ganancia nueva.

**Riesgo residual:** envenenamiento del corpus RAG compartido si no se activa `curators_only` en producción.

---

### A02 — Cryptographic Failures

| Campo | Valor |
|---|---|
| **Estado** | Parcialmente corregida |
| **Plan** | R-01, R-11 |
| **Severidad residual** | Medio |

**Evidencias de remediación**

- Validador en `Settings`: en producción (o `JWT_SECRET_ENFORCE=true`) aborta si el secreto es vacío, default o &lt; 32 chars (`settings.py`).
- Test `test_jwt_secret_en_produccion_rechaza_default` **passed**.
- bcrypt se mantiene; `.env.example` documenta generación de secreto.

**Evidencias de remediación incompleta**

- En desarrollo el secreto débil solo genera **WARNING**, no falla.
- Token sigue en `localStorage` por defecto (`frontend/src/api/client.js`, `VITE_AUTH_STORAGE` default `local`).
- No hay cookies `HttpOnly` / refresh token (R-11 solo parcial: opción `session` + CSP).

**Riesgo residual:** XSS sigue pudiendo exfiltrar JWT; despliegues mal etiquetados como `development` evitan el enforce.

---

### A03 — Injection

| Campo | Valor |
|---|---|
| **Estado** | Parcialmente corregida |
| **Plan** | R-08 (+ R-05) |
| **Severidad residual** | Medio |

**Evidencias de remediación**

- Prompt con delimitadores `<<<CONSULTA_AGRICULTOR>>>` / fragmentos y anotación de patrones de inyección (`adaptador_generacion_ollama.py`).
- System prompt ampliado para ignorar instrucciones embebidas.
- Test `test_prompt_hardening_delimitadores_e_inyeccion` **passed**.
- SQLAlchemy ORM sin cambio regresivo evidenciado.

**Evidencias de remediación incompleta**

- Sigue siendo mitigación heurística: el texto de usuario/documentos entra al LLM.
- Con policy `open`, un usuario puede inyectar vía ingest al corpus.

**Riesgo residual:** prompt/knowledge poisoning no eliminado; solo reducido.

---

### A04 — Insecure Design

| Campo | Valor |
|---|---|
| **Estado** | Parcialmente corregida |
| **Plan** | R-03, R-05, R-06, R-13 |
| **Severidad residual** | Medio |

**Evidencias de remediación**

- Rate limiting login/register/queries (`rate_limit.py`, controladores).
- Políticas configurables de password y knowledge.
- Cuota suave en `/api/v1/queries`.

**Evidencias de remediación incompleta**

- Registro abierto sin verificación de correo (sin cambio).
- Sin tenancy real del conocimiento (solo gate de escritura opcional).
- Rate limit **en memoria de proceso**: no efectivo en múltiples réplicas; IP vía `X-Forwarded-For` sin validar proxy de confianza.

**Riesgo residual:** diseño multi-usuario privilegiado sigue débil si no se configuran flags.

---

### A05 — Security Misconfiguration

| Campo | Valor |
|---|---|
| **Estado** | Parcialmente corregida |
| **Plan** | R-04, R-12 |
| **Severidad residual** | Bajo-Medio |

**Evidencias de remediación**

- `docs_url` / `redoc` / `openapi` deshabilitados cuando no `openapi_habilitado` (`main.py`).
- Health mínimo `{status: ok}` cuando no `health_incluye_detalle` (`health_controller.py`).
- CORS con métodos/headers explícitos (`cors.py`: GET/POST/OPTIONS; Authorization/Content-Type/Accept).
- Tests CORS/settings/health de seguridad **passed**.

**Evidencias de remediación incompleta**

- En `APP_ENV=development` (default) OpenAPI y health detallado **siguen expuestos** (intencional, pero residual en demos públicas mal configuradas).
- Escucha `0.0.0.0` sin cambio.

**Riesgo residual:** exposición de superficie si producción no usa `APP_ENV=production`.

---

### A06 — Vulnerable and Outdated Components

| Campo | Valor |
|---|---|
| **Estado** | No corregida |
| **Plan** | R-10 |
| **Severidad residual** | Medio |

**Evidencias**

- `backend/requirements.txt` mantiene rangos abiertos (`fastapi>=0.115.0`, `chromadb>=0.5.23`, …).
- No hay `requirements.lock`, Dependabot/Renovate ni job `pip-audit`/`npm audit` en el repositorio (búsqueda sin hallazgos de implementación).
- Frontend conserva `package-lock.json` (ya existía; no es remediación nueva completa).

**Riesgo residual:** CVEs transitivos sin proceso de actualización demostrable.

---

### A07 — Identification and Authentication Failures

| Campo | Valor |
|---|---|
| **Estado** | Parcialmente corregida |
| **Plan** | R-01, R-03, R-06, R-11 |
| **Severidad residual** | Medio |

**Evidencias de remediación**

- Rate limit en login/register; logging `login_ok` / `login_fail`.
- `PASSWORD_POLICY=strong` implementado (mayúscula + dígito); test unitario **passed**.
- UI login maneja HTTP 429; registro informa política strong.

**Evidencias de remediación incompleta**

- Default `password_policy=basic` (solo longitud ≥ 8).
- Sin MFA, sin lockout persistente, sin revocación de JWT.
- Almacenamiento de token sigue expuesto a XSS (default localStorage).
- Tests E2E de login con MySQL **no ejecutados** en este entorno.

**Riesgo residual:** fuerza bruta mitigada solo parcialmente; sesiones robables vía XSS.

---

### A08 — Software and Data Integrity Failures

| Campo | Valor |
|---|---|
| **Estado** | Parcialmente corregida |
| **Plan** | R-09 |
| **Severidad residual** | Medio |

**Evidencias de remediación**

- `model_integrity.py` + `modelos.sha256.json` con hashes SHA-256.
- Verificación antes de `joblib.load` en clasificador y predictor.
- Enforce estricto solo si `model_integrity_check and es_produccion`.
- Test `test_integridad_modelo_conocido` **passed**.

**Evidencias de remediación incompleta**

- En desarrollo solo warning (si hash no coincide), no bloqueo.
- Sin firma criptográfica asimétrica ni CI de integridad de build.
- Ingest de conocimiento sin workflow de aprobación (salvo policy curator).

**Riesgo residual:** sustitución de artefactos en entornos no-prod; corpus sin revisión humana obligatoria.

---

### A09 — Security Logging and Monitoring Failures

| Campo | Valor |
|---|---|
| **Estado** | Corregida (alcance de aplicación; monitoreo externo pendiente) |
| **Plan** | R-02 |
| **Severidad residual** | Bajo-Medio |

**Evidencias de remediación**

- Módulo `security_logging.py` con logger `agro.security`.
- Eventos: `login_ok`/`login_fail`, `register_ok`/`register_conflict`, `auth_denied`, `knowledge_ingest`/`index`/`forbidden`, `rate_limited`.
- Se evita loguear passwords/tokens; email parcialmente enmascarado.

**Evidencias de remediación incompleta (fuera del núcleo de app)**

- No hay SIEM, alertas, retención ni dashboards (Sentry/Prometheus no integrados).
- Para el alcance PMV1 de “trazas de seguridad en aplicación”, el hallazgo A09 de la auditoría 04 queda **cubierto**.

**Riesgo residual:** detección reactiva limitada sin stack de monitoreo.

---

### A10 — Server-Side Request Forgery (SSRF)

| Campo | Valor |
|---|---|
| **Estado** | Parcialmente corregida |
| **Plan** | R-07 |
| **Severidad residual** | Bajo |

**Evidencias de remediación**

- Allowlist de hosts para `SENAMHI_WIS2_BASE_URL` y `OLLAMA_BASE_URL` cuando enforce activo (`settings.py`).
- Enforce automático en producción (`url_allowlist_enforce is None → es_produccion`).

**Evidencias de remediación incompleta**

- Default de desarrollo: allowlist **no** enforce.
- Weather público por defecto amplifica abuso hacia el destino permitido.
- Embedding externo aún no implementa HTTP (riesgo futuro).

**Riesgo residual:** bajo si producción usa defaults de enforce; medio si se desactiva allowlist.

---

## Controles mal implementados / limitaciones observadas

| Hallazgo | Severidad | Evidencia |
|---|---|---|
| Defaults “abiertos” dejan remediaciones inactivas en demos | Alto operativo | `knowledge_mutation_policy=open`, `password_policy=basic`, `weather_require_auth=false` |
| Rate limit solo en memoria + confianza en `X-Forwarded-For` | Medio | `auth_controller._cliente_ip`, `LimitadorVentana` |
| CSP de frontend con `connect-src ... https:` amplio | Bajo-Medio | `frontend/index.html` |
| R-10 (deps) no implementado | Medio | `requirements.txt` sin lock/audit CI |
| R-11 sin HttpOnly cookies | Medio | `client.js` sigue en web storage |

## Posibles nuevas vulnerabilidades / regresiones

| Ítem | Evaluación |
|---|---|
| Regresión funcional por OpenAPI off | Solo en `production`; development conserva `/openapi.json` (test passed) |
| Regresión health | Detalle MySQL oculto solo fuera de desarrollo; test health desarrollo passed |
| Contaminación de estado en test de roles | El test muta `container.settings` (riesgo de flaky tests, no de prod) |
| Dependencia de MySQL para validar login/roles | Entorno actual no permite cerrar evidencia dinámica de esos flujos |

No se observó eliminación de endpoints de negocio ni cambio incompatible del contrato JSON principal (campos nuevos aditivos: `role`).

---

## Matriz consolidada post-implementación

| ID | Categoría | Estado implementación | Score parcial (0–10) | Score previo (04) |
|---|---|---|---|---|
| A01 | Broken Access Control | Parcial | 5 | 3 |
| A02 | Cryptographic Failures | Parcial | 5 | 3 |
| A03 | Injection | Parcial | 6 | 5 |
| A04 | Insecure Design | Parcial | 5 | 3 |
| A05 | Security Misconfiguration | Parcial | 7 | 3 |
| A06 | Vulnerable Components | No corregida | 5 | 5 |
| A07 | Authentication Failures | Parcial | 6 | 3 |
| A08 | Integrity Failures | Parcial | 6 | 5 |
| A09 | Logging Failures | Corregida* | 7 | 2 |
| A10 | SSRF | Parcial | 8 | 7 |
| | **Score global** | | **60 / 100** | **38 / 100** |

\*Corregida a nivel de logging de aplicación; monitoreo externo sigue ausente (riesgo residual bajo-medio).

---

## Checklist de activación segura en producción (no es remediación nueva)

Para que el score operativo se acerque al potencial del código, la evidencia exige como mínimo:

```env
APP_ENV=production
JWT_SECRET=<≥32 chars, no default>
KNOWLEDGE_MUTATION_POLICY=curators_only
KNOWLEDGE_CURATOR_EMAILS=...
PASSWORD_POLICY=strong
WEATHER_REQUIRE_AUTH=true
RATE_LIMIT_ENABLED=true
MODEL_INTEGRITY_CHECK=true
URL_ALLOWLIST_ENFORCE=true
```

Sin esa configuración, **varias vulnerabilidades del informe 04 permanecen explotables** pese a existir el código de control.

---

## Conclusión

La implementación **sí materializa** la mayoría de ítems del plan (R-01…R-09, R-12, R-13; R-10 no; R-11 parcial). El proyecto pasó de **38 a 60/100**: mejora sustancial, especialmente en logging, misconfiguración y controles condicionales de auth/conocimiento.

No puede declararse “OWASP Top 10 cerrado”: **8 de 10 categorías siguen parciales**, **A06 no corregida**, y los defaults compatibles con demos mantienen riesgo residual alto si se despliegan sin endurecer flags. La verificación dinámica completa de login/roles/API quedó **bloqueada en este entorno por MySQL caído**; la evidencia estática y 11 tests unitarios de seguridad respaldan los controles no dependientes de BD.
