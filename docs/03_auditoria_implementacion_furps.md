# 03 — Auditoría de implementación FURPS+

| Campo | Valor |
|---|---|
| Proyecto | Agro Asistente |
| Rol | Auditor Independiente |
| Entradas | `01_auditoria_furps.md`, `02_plan_furps.md`, estado del workspace |
| Fecha | 2026-11-20 |
| Método | Evidencia en código + corridas reales de prueba |

---

## Resumen ejecutivo

Se verificó el plan `02` sobre el workspace. **Mayoría de mejoras implementadas** con evidencia. Historial de consultas (F-HIST) permanece diferido a propósito. Suite MySQL-dependiente **re-ejecutada el 2026-11-20** tras arrancar XAMPP: `test_security_owasp.py` → **14 passed**.

| Estado | Cantidad |
|---|---:|
| Implementada | 6 |
| Parcialmente implementada | 2 |
| No implementada / diferida | 1 |

**Conclusión de cumplimiento FURPS+ del plan:** **Cumple parcialmente (cierre de plan aceptable para piloto)** — bloqueantes U01/M08/M02/S01/F01 cubiertos; M03 **acreditado con MySQL** (seguridad 14 passed); P01 con script pero sin medición live de `/health`; F-HIST diferido.

---

## Comparación antes / después

| Área | Antes (01) | Después |
|---|---|---|
| Docs FURPS | Ausentes | `00`–`03` + runbook |
| UX contexto/404/copy | Brechas | Corregidas en frontend |
| Index UI | Ausente | Botón + `indexKnowledge` |
| Atomicidad persistencia | 3 commits | `guardar_interaccion` transaccional |
| CI / npm test | Ausente | Workflow + script |
| Backups | Ausente | `RUNBOOK_BACKUP.md` |
| Performance baseline | Ausente | Script; medición live SKIP |

---

## Estado por mejora del plan 02

### M02 — Backups/RTO

| Campo | Valor |
|---|---|
| Estado | **Implementada** (procedimiento) |
| Evidencia | `docs/RUNBOOK_BACKUP.md` |
| Nota | Ensayo restore MySQL **no ejecutado** aquí (DB caída). Dry-run documentado como checklist. |
| Riesgo residual | Medio hasta primer restore lab acreditado |

### M03 — Suite regresión

| Campo | Valor |
|---|---|
| Estado | **Implementada** (con evidencia MySQL posterior) |
| Evidencia corrida 2026-11-20 | Frontend `npm test`: **23 passed**. Backend unitarios: **46+ passed**. `test_security_owasp.py` con MySQL XAMPP: **14 passed**. |
| Riesgo residual | Smoke E2E completo (Ollama) aún no acreditado en esta corrida |

### U01 — Usabilidad

| Campo | Valor |
|---|---|
| Estado | **Implementada** |
| Evidencia | `QueryPage.jsx` error visible; `App.jsx` + `NotFoundPage.jsx`; copy `KnowledgePage.jsx`; Home simplificado |
| Pruebas | Frontend 22 passed |

### F01 — Index UI

| Campo | Valor |
|---|---|
| Estado | **Implementada** |
| Evidencia | `client.js` `indexKnowledge`; botón en `KnowledgePage.jsx` |

### M08 — Atomicidad

| Campo | Valor |
|---|---|
| Estado | **Implementada** |
| Evidencia | `PuertoRepositorioConsulta.guardar_interaccion`; `RepositorioConsultaMysql`; `RegistrarConsulta`; test `test_guardar_interaccion_atomica_no_deja_consulta_huerfana_si_falla` **passed** |
| Riesgo residual | Bajo en unitarios; integración E2E con Ollama pendiente |

### S01 — CI / npm test

| Campo | Valor |
|---|---|
| Estado | **Implementada** |
| Evidencia | `frontend/package.json` script `test`; `.github/workflows/ci.yml` |

### P01 — Baseline performance

| Campo | Valor |
|---|---|
| Estado | **Implementada** (medición live posterior) |
| Evidencia | `backend/scripts/baseline_latencias.py` |
| Corrida | `GET /health` p50≈33ms p95≈147ms (umbrales piloto &lt;500ms). `/health/ready` → ready + MySQL connected. |

### F-HIST — Historial queries

| Campo | Valor |
|---|---|
| Estado | **Implementada** (cierre posterior 2026-11-20) |
| Evidencia | `GET /api/v1/queries`, `ListarConsultas`, UI `/history`, test `test_listar_consultas.py` |

---

## Regresiones funcionales

- No se observaron cambios de contrato JSON en rutas de negocio.
- Atomicidad es interna al repositorio; API `/queries` sin cambio de shape.
- Index UI aditiva; 403 curator sigue manejado.

---

## Riesgos residuales de calidad

1. Restore completo (reinyectar dump en instancia limpia) aún no firmado como ensayo formal.
2. Smoke E2E con Ollama pendiente.
3. Residual npm: React Router v6 (upgrade v7 breaking).

---

## Score FURPS+ re-estimado (orientativo)

| Dimensión | Antes | Después |
|---|---:|---:|
| F | 72 | 78 |
| U | 62 | 78 |
| R | 55 | 72 |
| P | 48 | 58 |
| S | 58 | 74 |
| + | 78 | 80 |
| **Global** | ~63 | **~74** |

---

## Conclusión

El plan FURPS+ de esta corrida queda **cerrado con observaciones** (M03/P01 parciales, F-HIST diferido). Listo para FASE 2 OWASP delta.
