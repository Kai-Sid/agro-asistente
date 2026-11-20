# 07 — Auditoría final integral

| Campo | Valor |
|---|---|
| Proyecto | Agro Asistente (`Kai-Sid/agro-asistente`) |
| Rol | Auditor Principal de Calidad y Seguridad |
| Fecha | 2026-11-20 (actualizado cierre P1) |
| Entradas | `03_auditoria_implementacion_furps.md`, `06_auditoria_implementacion_owasp.md`, estado del workspace |
| Rama | `owasp` |
| Alcance | PMV1 + plan maestro FURPS+/OWASP ejecutado en esta corrida |

---

## 1. Resumen ejecutivo

Se ejecutaron las tres fases del plan maestro (`00`): auditoría/mejora FURPS+, delta OWASP residual, y validación documental con pruebas parciales reales.

| Dimensión | Veredicto |
|---|---|
| Calidad (FURPS+) | **Cumple parcialmente** (score orientativo ~74/100; plan 02 cerrado con observaciones) |
| Seguridad (OWASP Top 10) | **Cumple parcialmente** (score **68/100**; A06 ya no “no corregida”) |
| Funcionalidad | **Se preservó** el PMV1; cambios aditivos (UI index, atomicidad, flags) |
| Riesgo operativo | **Medio** con checklist + endurecimiento en código; **Alto** solo si se fuerza bypass lab |
| **Recomendación final** | **Apto para producción con observaciones** (piloto académico / despliegue controlado) |

“Producción” = piloto controlado, no servicio masivo de asesoría agronómica oficial.

---

## 2. Estado de calidad (FURPS+)

### Veredicto: Cumple parcialmente

Fundamento (`03`):

- Implementadas: M02 runbook, U01 UX, F01 index UI, M08 atomicidad, S01 CI/npm test.
- Cerrados después: F-HIST (historial UI/API), P01 (baseline `/health` live), backup script + ensayo dump, `/health/ready`.
- M03: **acreditado** con MySQL (`test_security_owasp.py` **14 passed**).
- Cierre P1: restore lab acreditado (`restore_ensayo.ps1`), defaults demo bloqueados en `APP_ENV=production`.

Evidencias de prueba registradas:

- Frontend `npm test`: **23 passed**.
- Backend unitarios (subset): **46+ passed**.
- Seguridad con MySQL: **14 passed** (`test_security_owasp.py`).

---

## 3. Estado de seguridad (OWASP)

### Veredicto: Cumple parcialmente

| Indicador | Valor |
|---|---|
| Score 04 histórico | 38 |
| Score 06 previo | 60 |
| Score 06 actual | **68** |
| Categorías “no corregidas” | **0** |
| Parciales | 9 |
| Corregida | 1 (A09) |

Condición operativa (go): aplicar `docs/CHECKLIST_PRODUCCION.md` completo. En production el arranque **falla** si faltan curators / password strong / weather auth / rate limit (ver `settings.py`).

```env
APP_ENV=production
JWT_SECRET=<≥32 chars>
KNOWLEDGE_MUTATION_POLICY=curators_only
KNOWLEDGE_CURATOR_EMAILS=...
PASSWORD_POLICY=strong
WEATHER_REQUIRE_AUTH=true
RATE_LIMIT_ENABLED=true
MODEL_INTEGRITY_CHECK=true
URL_ALLOWLIST_ENFORCE=true
AUTH_COOKIE_ENABLED=true
AUTH_COOKIE_SECURE=true
```

Frontend build: `VITE_AUTH_STORAGE=session` y `VITE_AUTH_COOKIE_MODE=true` (Render).

---

## 4. Funcionalidad

### Veredicto: Se preservó

| Criterio | Evaluación |
|---|---|
| Procesos de negocio PMV1 | Intactos (auth, contextos, query RAG, knowledge, clima, riesgo) |
| Regresiones observadas | No evidenciadas en contratos principales |
| Riesgos de regresión | Activar flags harden sin curadores / password strong / weather auth |

Smoke E2E: script + pytest listos (`scripts/smoke_e2e_ollama.py`). Corrida live pendiente si API/Ollama no están arriba; ver `EVIDENCIA_CIERRE_P1.md`.

---

## 5. Riesgo operativo

| Escenario | Riesgo | Estado 2026-11-20 |
|---|---|---|
| Piloto aula + checklist + production enforce | **Medio** | Controles en código + Render |
| Público con `.env` demo / `APP_ENV=production` incompleto | **Mitigado** | Arranque rechazado si faltan curators/strong/weather/rate limit |
| Decisiones agronómicas críticas / HU-08 como verdad | **Mitigado en contrato** | API fuerza `es_riesgo_agricola_validado=false` + `aviso_no_oficial`; UI refuerza aviso |

---

## 6. Riesgos pendientes priorizados

| Pri | Riesgo | Estado |
|---|---|---|
| P1 | Defaults demo si se ignora checklist | **Cerrado en production** (validator Settings) |
| P1 | Primer restore de backup aún no ensayado en lab | **Acreditado** — `restore_ensayo.ps1` → 6 tablas lab |
| P1 | Smoke E2E con Ollama automatizado | **Herramienta lista**; corrida live cuando servicios estén up |
| P2 | CVEs transitivos (chromadb/ragas/npm–Vite/esbuild) | Abierto / documentado `SUPPLY_CHAIN.md` |
| P2 | Cookie HttpOnly | **Disponible**; Render la activa; local default false (compat) |
| P2 | Residual `esbuild`/Vite 5 | Abierto (upgrade Vite 8 breaking) |
| P3 | Cola async en memoria | Aceptado PMV1 |

Detalle: `docs/EVIDENCIA_CIERRE_P1.md`.

---

## 7. Observaciones

1. Trazabilidad metodológica completa en `docs/00`–`07`.
2. FURPS y OWASP avanzaron en la misma rama `owasp` sin romper arquitectura hexagonal.
3. No se autoriza presentar el sistema como OWASP “completo” ni como asesor oficial.
4. Residual operativo menor: pegar salida `[PASS]` del smoke Ollama live cuando staging esté disponible; CVEs transitivos.

---

## 8. Recomendación final

**Apto para producción con observaciones.**

Condiciones mínimas antes de piloto externo:

1. Checklist de producción cumplido (ahora también **enforce** en código si `APP_ENV=production`).  
2. Backup MySQL + knowledge tomados (**restore lab acreditado**).  
3. Ejecutar smoke E2E con MySQL + Ollama y archivar `[PASS]`.  
4. Curator configurado (`KNOWLEDGE_CURATOR_EMAILS` obligatorio en production).  

Si se usa `APP_ENV=development` con defaults demo, el dictamen aplica solo a **laboratorio local**.
