# 00 — Plan maestro FURPS+ y OWASP — Agro Asistente

| Campo | Valor |
|---|---|
| Proyecto | Agro Asistente (`Kai-Sid/agro-asistente`) |
| Rama base | `owasp` |
| Commit de arranque | `ae106ea` |
| Fecha | 2026-11-20 |
| Alcance | Auditoría, mejora y validación de calidad (FURPS+) y seguridad (OWASP Top 10) |
| Restricciones | Compatibilidad hacia atrás; no romper PMV1; evidencias observables; no declarar pruebas exitosas sin ejecutarlas |

---

## 1. Diagnóstico técnico

### Stack verificado

| Capa | Tecnología | Evidencia |
|---|---|---|
| Arquitectura | Hexagonal (domain / application / infrastructure) | `docs/ARQUITECTURA.md`, `backend/app/` |
| Backend | FastAPI + SQLAlchemy + Pydantic Settings | `backend/app/main.py`, `settings.py` |
| Frontend | React 18 + Vite + React Router + Axios | `frontend/src/App.jsx` |
| BD | MySQL/MariaDB (schema en español) | `database/schema.sql` |
| Auth | JWT HS256 + bcrypt + claim `role` | auth/JWT/bcrypt adapters |
| RAG | Chunking + embeddings léxicos + Chroma + Ollama/Qwen2.5 | knowledge/query adapters |
| Extra | Weather SENAMHI, clasificación TF-IDF, riesgo HU-08 | controllers + docs HU08 |

### APIs

- `POST /api/v1/auth/register`, `POST /api/v1/auth/login`
- `GET\|POST /api/v1/contexts`, `POST /api/v1/contexts/{id}/select`
- `POST /api/v1/queries`
- `POST /api/v1/knowledge/ingest\|index`, `GET /api/v1/knowledge/documents`
- `GET /api/v1/weather/observations`
- `POST /api/v1/clasificacion`, `POST /api/v1/riesgo`
- `GET /health`

### Estado metodológico al inicio

| Artefacto | Estado al arranque (`ae106ea`) |
|---|---|
| `00_plan_maestro_furps_owasp.md` | Este documento |
| `01`–`03` FURPS | Ausentes → se generan en FASE 1 |
| `04`–`06` OWASP | Presentes (score 38→60/100) → delta en FASE 2 |
| `07` final | Presente (2026-11-13) → se reemite en FASE 3 |

**Conclusión:** pista OWASP avanzada con remediaciones por flags; pista FURPS+ sin trazabilidad en Git.

---

## 2. Inventario de módulos

| ID | Área | Rutas clave |
|---|---|---|
| M-AUTH | Auth | `auth_controller.py`, JWT/bcrypt, `frontend/src/api/client.js` |
| M-CTX | Contextos | `context_controller.py`, repos MySQL, `ContextPage.jsx` |
| M-QRY | Consultas RAG | `query_controller.py`, `submit_query.py`, Ollama, `QueryPage.jsx` |
| M-KNOW | Conocimiento | `knowledge_controller.py`, Chroma, `KnowledgePage.jsx` |
| M-WX | Clima | `weather_controller.py`, SENAMHI |
| M-ML | Clasificación / riesgo | clasificacion/riesgo + joblib |
| M-SEC | Controles seguridad | `settings.py`, auth deps, CORS, rate limit, logging |
| M-DB | Schema / repos | `database/schema.sql`, adapters MySQL |
| M-QA | Pruebas | `backend/tests/*`, `frontend/src/**/*.test.js` |
| M-OPS | Docs / deploy | `docs/*`, `render.yaml`, `.env.example` |

---

## 3. Matriz FURPS+ (evaluación planificada)

| Dimensión | Brechas preliminares | Evidencias a producir |
|---|---|---|
| F Functionality | Sin historial GET queries; UI sin index; HU-08 experimental; RAGAS sin scores | Matriz HU vs código; smoke E2E |
| U Usability | Catch vacío contexto; sin 404; health técnico en Home; copy Knowledge vs RAG | Heurística UX; checklist a11y básico |
| R Reliability | Persistencia no atómica; sin backups/RTO; health/ready parcial | Transacciones; runbook backup |
| P Performance | Index síncrono; timeouts Ollama; sin benchmarks | Script timings; umbrales piloto |
| S Supportability | Sin CI; rangos en requirements; docs FURPS ausentes; sin script npm test | CI mínimo; pin/lock; docs 01–03 |
| + Design | Hexagonal OK; drift nombres EN docs vs ES schema | `test_architecture.py` |

---

## 4. Matriz OWASP Top 10 (baseline rama `owasp`)

| Cat. | Estado 06 | Residual | Acción FASE 2 |
|---|---|---|---|
| A01 | Parcial | Defaults `open` / weather público | Curator prod-like + tests |
| A02 | Parcial | JWT en web storage | R-11 política storage |
| A03 | Parcial | Prompt/RAG poisoning | Hardening + política ingest |
| A04 | Parcial | Registro abierto; tenancy knowledge | Threat model / cuotas |
| A05 | Parcial | Defaults demo en deploy | Checklist prod / render |
| A06 | No corregida | Sin pin/audit | R-10 lock + audit |
| A07 | Parcial | Password `basic` default | Validar strong + rate limit |
| A08 | Parcial | Solo joblib | Checklist integridad |
| A09 | Corregida | Sin SIEM | Mantener |
| A10 | Parcial | Allowlist ligada a `APP_ENV` | Tests allowlist |

Scores documentados: **38 → 60 / 100**. Meta: **≥ 70** con flags prod + cierre A06.

---

## 5. Riesgos priorizados

| Pri | Riesgo |
|---|---|
| P1 | Controles OWASP inactivos con defaults demo |
| P1 | Corpus RAG alterable si knowledge `open` |
| P1 | Sin backups/RTO acreditados |
| P1 | Suite MySQL-dependiente no siempre ejecutable |
| P2 | A06 supply chain; persistencia no atómica; JWT en storage; docs FURPS ausentes |
| P3 | Index síncrono / latencia Ollama; HU-08/RAGAS no validados en campo |

---

## 6. Herramientas

- Calidad: pytest, `node --test`, checklist FURPS, smoke E2E.
- Seguridad: `test_security_owasp.py`, pip-audit/npm audit, checklist env.
- Rendimiento: script de latencia sobre `/queries` e index.
- Ops: checklist `APP_ENV=production` + flags endurecidos.

---

## 7. Fases de ejecución

### FASE 1 — FURPS+

1. `01_auditoria_furps.md` con puntajes y evidencias.
2. `02_plan_furps.md` con mejoras Mxx, rollback y orden.
3. Implementar: backups (M02), suite/CI (M03/S01), UX (U01), atomicidad (M08), index UI o decisión (F01), baseline perf (P01).
4. `03_auditoria_implementacion_furps.md`.

### FASE 2 — OWASP (delta)

1. Revalidar/actualizar `04` y delta en `05`.
2. Cerrar residuales: A06/R-10, R-11, checklist prod (O-CFG), curator (O-A01).
3. Actualizar `06` + score.

### FASE 3 — Validación integral

1. Smoke/regresión flags off/on.
2. Reescribir `07_auditoria_final.md` con dictamen.

---

## 8. Orden de prioridades

1. Plan maestro 00 (este documento).
2. FURPS 01 → 02.
3. Backups + suite MySQL / CI.
4. UX de bajo riesgo (U01).
5. Atomicidad persistencia (M08).
6. Re-auditoría OWASP + A06 + checklist prod + curator.
7. Residual R-11 y performance.
8. Auditorías 03, 06 actualizado, 07 nuevo.

---

## 9. Estrategia de pruebas

| Capa | Qué | Cuándo |
|---|---|---|
| Backend | pytest + seguridad | Cada mejora |
| Frontend | `node --test` | Tras UX/auth storage |
| Seguridad | `test_security_owasp.py` (+ MySQL) | Cierre 06 |
| Smoke E2E | Flujo agricultor | FASE 3 |
| Negativas | 401/403/429, 503 Ollama | OWASP + Reliability |

**Regla:** no declarar verde sin log de ejecución.

---

## 10. Criterios de aceptación globales

- Existen `docs/00`–`07` con evidencias citadas.
- FURPS `03` clasifica cada ítem de `02` sin asumir.
- OWASP score actualizado; A06 con plan/evidencia; demo vs prod explícito.
- PMV1 preservado en modo desarrollo (flags compatibles).
- `07` emite: apto / apto con observaciones / no apto, con condiciones.
- Sin cambio de arquitectura hexagonal ni eliminación de HUs.

---

## 11. Archivos candidatos a modificación posterior

- Docs: `docs/00`–`07`, `docs/INSTALACION.md`, runbooks.
- FURPS: `QueryPage.jsx`, `App.jsx`, `KnowledgePage.jsx`, `HomePage.jsx`, repos/use cases query, `package.json`, `.github/workflows/*`.
- OWASP: `settings.py`, `render.yaml`, `.env.example`, `requirements.txt` (+ lock), `client.js`, tests seguridad.

**Fuera de alcance sin decisión explícita:** schema destructivo, eliminar endpoints, reescribir RAG core, fine-tuning.
