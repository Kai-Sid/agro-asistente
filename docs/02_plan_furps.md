# 02 — Plan de mejora FURPS+

| Campo | Valor |
|---|---|
| Proyecto | Agro Asistente |
| Entrada | `docs/01_auditoria_furps.md` (score ~63/100) |
| Rol | Arquitecto de Software |
| Fecha | 2026-11-20 |
| Restricción | El sistema ya funciona; compatibilidad hacia atrás; rollback; validación obligatoria |

---

## Principios

1. Cambios incrementales sin eliminar HUs ni romper contratos JSON.
2. Preferir documentación + flags antes que reescrituras.
3. Toda mejora con prueba o evidencia observable.
4. Rollback = revert de commit o desactivar feature aditiva.

---

## Roadmap

```text
Fase A  Docs/ops críticos     → M02 backups, M03 registro de suite
Fase B  UX bajo riesgo        → U01, F01 (index UI)
Fase C  Fiabilidad datos      → M08 atomicidad
Fase D  Supportability/perf   → S01 CI + npm test, P01 baseline
Fase E  Verificación          → 03_auditoria_implementacion_furps.md
```

### Orden recomendado

| Orden | ID | Mejora | Prioridad |
|---|---|---|---|
| 1 | M02 | Runbook backup/restore MySQL + Chroma | Crítica |
| 2 | M03 | Ejecutar/registrar pytest (+ nota MySQL) | Crítica |
| 3 | U01 | UX: errores contexto, 404, copy Knowledge/Home | Alta |
| 4 | F01 | Botón indexación en Knowledge UI | Media |
| 5 | M08 | Persistencia atómica consulta+respuesta+evidencias | Alta |
| 6 | S01 | `npm test` + workflow CI mínimo | Media |
| 7 | P01 | Script baseline latencias + tabla umbrales | Media |
| 8 | F-HIST | Historial GET queries + UI `/history` | Baja → **implementada** (2026-11-20) |

**Decisión F01/F-HIST:** indexación en UI (HU-06) e historial de consultas (`GET /api/v1/queries` + `/history`) quedaron implementados.

---

## Mejoras detalladas

### M02 — Backups y RTO

| Campo | Detalle |
|---|---|
| Objetivo | Procedimiento reproducible de backup/restore |
| Justificación | Reliability crítica (01) |
| Prioridad | Crítica |
| Riesgo | Bajo (solo docs/scripts no destructivos) |
| Componentes | `docs/RUNBOOK_BACKUP.md`, opcional `database/scripts/` |
| Validación | Ensayo restore en lab o checklist dry-run documentado |
| Rollback | Eliminar runbook/scripts |

### M03 — Suite de regresión acreditada

| Campo | Detalle |
|---|---|
| Objetivo | Registrar corrida pytest (y frontend tests) con resultado real |
| Prioridad | Crítica |
| Validación | Log en `03` o anexo; no inventar passed |
| Rollback | N/A |

### U01 — Usabilidad

| Campo | Detalle |
|---|---|
| Objetivo | Errores visibles de contexto; ruta 404; copy alineado; Home menos técnico |
| Componentes | `QueryPage.jsx`, `App.jsx`, `KnowledgePage.jsx`, `HomePage.jsx`, `NotFoundPage.jsx` |
| Prioridad | Alta |
| Riesgo | Bajo |
| Validación | `node --test` + smoke visual |
| Rollback | Revert archivos UI |

### F01 — Indexación en UI

| Campo | Detalle |
|---|---|
| Objetivo | Exponer `POST /api/v1/knowledge/index` desde Knowledge |
| Componentes | `client.js`, `KnowledgePage.jsx` |
| Prioridad | Media |
| Riesgo | Medio (403 curator si política activa) — mostrar mensaje |
| Validación | Smoke UI; manejo 403 |
| Rollback | Quitar botón/API client |

### M08 — Atomicidad

| Campo | Detalle |
|---|---|
| Objetivo | Una transacción para consulta + respuesta + evidencias |
| Componentes | `PuertoRepositorioConsulta`, `RepositorioConsultaMysql`, `RegistrarConsulta`, fakes de test |
| Prioridad | Alta |
| Riesgo | Medio (persistencia) — mantener contratos API |
| Validación | Unit test: fallo simulado no deja consulta huérfana; suite submit |
| Rollback | Restaurar tres `guardar_*` separados |

### S01 — Supportability tests/CI

| Campo | Detalle |
|---|---|
| Objetivo | Script `npm test` + `.github/workflows/ci.yml` mínimo |
| Prioridad | Media |
| Validación | Workflow válido; tests locales |
| Rollback | Quitar workflow/script |

### P01 — Baseline performance

| Campo | Detalle |
|---|---|
| Objetivo | Script de timings y umbrales piloto documentados |
| Componentes | `backend/scripts/baseline_latencias.py`, nota en `03` |
| Prioridad | Media |
| Validación | Ejecución opcional (sin Ollama = documentar skip) |
| Rollback | Eliminar script |

### F-HIST — Historial (diferido)

| Campo | Detalle |
|---|---|
| Objetivo | `GET /queries` + UI |
| Prioridad | Baja |
| Estado | **No implementar** en esta corrida; aceptar deuda en `03` |

---

## Estrategia de preservación de funcionalidad

- No cambiar paths ni JSON de respuestas de negocio.
- Atomicidad interna transparente al cliente.
- Index UI aditivo.
- CI no altera runtime.

## Riesgos de ejecución

| Riesgo | Mitigación |
|---|---|
| MySQL ausente en entorno de auditoría | Registrar skipped/failed reales; no fingir |
| `curators_only` bloquea index en demos | Mensaje 403 claro; default `open` en dev |
| Regresión en fakes de test al cambiar puerto | Actualizar todos los fakes `guardar_interaccion` |
