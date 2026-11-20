# 04 — Auditoría OWASP Top 10

| Campo | Valor |
|---|---|
| Proyecto | `Kai-Sid/agro-asistente` |
| Alcance | Frontend React/Vite, backend FastAPI hexagonal, MySQL, Chroma, Ollama, SENAMHI, `render.yaml` |
| Metodología | OWASP Top 10 (2021) — revisión estática + evidencias de tests |
| Restricciones | Evaluación con evidencias; no inventar vulnerabilidades |

## Historial de versiones del informe

| Fecha | Commit / estado | Score | Nota |
|---|---|---:|---|
| 2026-11-13 | `eaac3da` (baseline pre-remediación en `main`) | **38 / 100** | Auditoría inicial (se conserva el detalle histórico abajo como contexto) |
| 2026-11-13 | Workspace con R-01…R-13 (rama `owasp`) | 60 / 100 | Ver `06` de esa fecha |
| **2026-11-20** | `owasp` + delta FURPS/A06/R-11/checklist | **Re-auditoría** → ver sección A | Dictamen cuantitativo actualizado en `06` |

---

## A. Re-auditoría 2026-11-20 (estado actual)

### Resumen

Los controles aditivos por flags (JWT enforce, rate limit, roles curator, CORS, prompt hardening, integridad joblib, logging) **siguen presentes**. El delta de esta corrida cierra huecos de **A06 (parcial)**, **R-11 (session en PROD)**, **checklist/render prod** y valida curator como requisito operativo documentado.

| Categoría | Estado 2026-11-20 | Severidad residual |
|---|---|---|
| A01 Broken Access Control | Parcial | Medio (defaults demo `open`) |
| A02 Cryptographic Failures | Parcial | Bajo–Medio (HttpOnly opcional vía `AUTH_COOKIE_*`; sessionStorage en PROD) |
| A03 Injection | Parcial | Medio (prompt/RAG residual) |
| A04 Insecure Design | Parcial | Medio |
| A05 Security Misconfiguration | Parcial → mejorado | Medio-Bajo con checklist/render |
| A06 Vulnerable Components | **Parcial** (antes: no corregida) | Medio (CVEs transitivos documentados) |
| A07 Authentication Failures | Parcial | Medio |
| A08 Software/Data Integrity | Parcial | Medio-Bajo |
| A09 Logging/Monitoring | Corregida (app) | Bajo |
| A10 SSRF | Parcial | Medio-Bajo |

### Evidencias delta

- Lock + auditoría: `backend/requirements.lock.txt`, `docs/SUPPLY_CHAIN.md`
- Session PROD: `frontend/src/api/client.js`, test en `baseUrl.test.js`
- Deploy: `render.yaml` (`APP_ENV=production`, policies harden), `docs/CHECKLIST_PRODUCCION.md`
- Knowledge curator: flags existentes + checklist; tests MySQL de roles **no re-ejecutados** (DB ausente)

### Score de esta pasada

El score numérico consolidado vive en `06_auditoria_implementacion_owasp.md` (**68 / 100** tras delta). Esta sección 04 no duplica remediaciones.

---

## B. Auditoría inicial 2026-11-13 (baseline histórico, score 38)

> Texto de referencia del hallazgo original sobre `eaac3da`. Útil para trazabilidad del plan R-01…R-13.

### Resumen ejecutivo (histórico)

El PMV1 aplicaba controles básicos (JWT, bcrypt, ORM, aislamiento de contextos, CORS acotado). Riesgos: secreto JWT por defecto, knowledge sin roles, weather público, sin logging/rate limit, OpenAPI expuesto, `joblib` sin integridad.

**Score global histórico: 38 / 100**

### A01 — Broken Access Control (histórico)

Knowledge compartido sin roles; weather público; contextos sí aislados por JWT.

### A02 — Cryptographic Failures (histórico)

bcrypt OK; JWT default inseguro; token en `localStorage`.

### A03 — Injection (histórico)

SQL bajo riesgo vía ORM; prompt injection RAG residual.

### A04 — Insecure Design (histórico)

Registro abierto; sin RBAC; sin rate limit; knowledge global.

### A05 — Security Misconfiguration (histórico)

OpenAPI/docs; health con detalle MySQL; secretos por defecto.

### A06 — Vulnerable Components (histórico)

Rangos abiertos; sin lock/audit.

### A07 — Authentication Failures (histórico)

Sin rate limit/lockout; password mínima débil; JWT largo sin revocación.

### A08 — Software and Data Integrity Failures (histórico)

`joblib.load` sin checksum.

### A09 — Logging and Monitoring Failures (histórico)

Sin logging de seguridad.

### A10 — SSRF (histórico)

URL SENAMHI/Ollama configurables sin allowlist estricta.

### Notas positivas históricas

1. Arquitectura hexagonal.
2. bcrypt + JWT con `exp`.
3. Ownership de contextos + tests.
4. ORM SQLAlchemy.
5. CORS sin `*` literal.
6. `.gitignore` de `.env`.
7. Render secrets `sync: false`.
