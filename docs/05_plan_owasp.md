# 05 — Plan de remediación OWASP Top 10

| Campo | Valor |
|---|---|
| Proyecto | `Kai-Sid/agro-asistente` |
| Entrada | `docs/04_auditoria_owasp.md` |
| Rol | Arquitecto de Seguridad |
| Fechas | 2026-11-13 (plan base R-01…R-13) · **delta 2026-11-20** |

## Principios

1. Compatibilidad hacia atrás vía feature flags (defaults demo en local).
2. Cambios aditivos; rollback por env/flag o revert.
3. No romper contratos de negocio PMV1.
4. Validación con tests existentes + nuevos de seguridad.

---

## Plan base R-01 … R-13 (2026-11-13)

| ID | Hallazgo | Prioridad | Estado tras rama `owasp` |
|---|---|---|---|
| R-01 | JWT secret enforce | Crítico | Aplicado |
| R-02 | Logging seguridad | Alto | Aplicado |
| R-03 | Rate limit auth | Alto | Aplicado |
| R-04 | OpenAPI/health harden | Alto | Aplicado |
| R-05 | Knowledge roles/flag | Alto | Aplicado |
| R-06 | Password policy | Alto | Aplicado |
| R-07 | Weather auth + allowlist | Medio | Aplicado |
| R-08 | Prompt hardening | Medio | Aplicado |
| R-09 | Checksum joblib | Medio | Aplicado |
| R-10 | Pinning + audit deps | Medio | **Delta 2026-11-20** |
| R-11 | Token fuera de localStorage | Medio | **Delta 2026-11-20** |
| R-12 | CORS explícito | Bajo | Aplicado |
| R-13 | Cuotas queries | Bajo | Aplicado |

Detalle original de mitigación/validación/rollback por ítem: se mantiene en el historial de commits de la rama `owasp` y en `06_remediacion_owasp_aplicada.md`.

---

## Delta 2026-11-20 (residuales)

### O-R10 — A06 supply chain

| Campo | Detalle |
|---|---|
| Riesgo | Dependencias con rangos abiertos y CVEs desconocidos |
| Prioridad | Alta |
| Mitigación | `requirements.lock.txt`; rangos acotados en `requirements.txt`; `docs/SUPPLY_CHAIN.md` con `pip-audit`/`npm audit` |
| Validación | Lock presente; informe supply chain con hallazgos reales |
| Rollback | Volver a instalar solo `requirements.txt` sin lock |
| Criterio | A06 al menos **parcial** con evidencia |

### O-R11 — Sesión / XSS

| Campo | Detalle |
|---|---|
| Riesgo | JWT en `localStorage` exfiltrable vía XSS |
| Prioridad | Media |
| Mitigación | Default `sessionStorage` en build PROD; `VITE_AUTH_STORAGE`; CSP existente; Render `VITE_AUTH_STORAGE=session` |
| Validación | Test fuente `baseUrl.test.js`; smoke login |
| Rollback | `VITE_AUTH_STORAGE=local` |
| Nota | Cookies HttpOnly siguen fuera de alcance (sin backend de cookie session) |

### O-CFG — Defaults de despliegue

| Campo | Detalle |
|---|---|
| Riesgo | Demo flags en hosting público |
| Prioridad | Crítica (ops) |
| Mitigación | `render.yaml` con `APP_ENV=production` + policies harden; `docs/CHECKLIST_PRODUCCION.md` |
| Validación | Checklist go/no-go; arranque prod sin secreto falla (test settings existente) |
| Rollback | Quitar vars del blueprint (local `.env` intacto) |

### O-A01 — Curator en prod-like

| Campo | Detalle |
|---|---|
| Riesgo | Corpus RAG envenenable si `open` |
| Prioridad | Alta |
| Mitigación | Checklist + `KNOWLEDGE_MUTATION_POLICY=curators_only` en Render; emails sync:false |
| Validación | Test roles (requiere MySQL); procedimiento documentado |
| Rollback | `open` en demo local |

---

## Orden delta

1. O-CFG checklist + render  
2. O-R10 lock/audit  
3. O-R11 session PROD  
4. O-A01 documentar/activar curator en prod  
5. Re-emitir `06` con score  

## Preservación de funcionalidad

Local/demo conserva defaults permisivos (`PASSWORD_POLICY=basic`, `KNOWLEDGE_MUTATION_POLICY=open`, `WEATHER_REQUIRE_AUTH=false`). El endurecimiento es **explícito** vía env / Render.
