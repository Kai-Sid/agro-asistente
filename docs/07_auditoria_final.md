# 07 — Auditoría final integral

| Campo | Valor |
|---|---|
| Proyecto | Agro Asistente (`Kai-Sid/agro-asistente`) |
| Rol | Auditor Principal de Calidad y Seguridad |
| Fecha | 2026-11-20 |
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
| Riesgo operativo | **Medio** con checklist de producción; **Alto** con defaults demo públicos |
| **Recomendación final** | **Apto para producción con observaciones** (piloto académico / despliegue controlado) |

“Producción” = piloto controlado, no servicio masivo de asesoría agronómica oficial.

---

## 2. Estado de calidad (FURPS+)

### Veredicto: Cumple parcialmente

Fundamento (`03`):

- Implementadas: M02 runbook, U01 UX, F01 index UI, M08 atomicidad, S01 CI/npm test.
- Cerrados después: F-HIST (historial UI/API), P01 (baseline `/health` live), backup script + ensayo dump, `/health/ready`.
- M03: **acreditado** con MySQL (`test_security_owasp.py` **14 passed**).

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

Condición operativa (go): aplicar `docs/CHECKLIST_PRODUCCION.md` completo.

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
```

Frontend build: `VITE_AUTH_STORAGE=session` (o vacío en PROD).

---

## 4. Funcionalidad

### Veredicto: Se preservó

| Criterio | Evaluación |
|---|---|
| Procesos de negocio PMV1 | Intactos (auth, contextos, query RAG, knowledge, clima, riesgo) |
| Regresiones observadas | No evidenciadas en contratos principales |
| Riesgos de regresión | Activar flags harden sin curadores / password strong / weather auth |

Smoke recomendado (matriz V-REG) — **no ejecutado E2E completo aquí** (API/MySQL/Ollama no levantados):

1. register → login → context → query → knowledge list/index  
2. Repetir con flags prod en staging  

---

## 5. Riesgo operativo

| Escenario | Riesgo |
|---|---|
| Piloto aula + checklist | **Medio** |
| Público con `.env` demo | **Alto** |
| Decisiones agronómicas críticas / HU-08 como verdad | **Alto** (RAGAS/HU-08 no validados en campo) |

---

## 6. Riesgos pendientes priorizados

| Pri | Riesgo |
|---|---|
| P1 | Defaults demo si se ignora checklist |
| P1 | Primer restore de backup aún no ensayado en lab |
| P1 | Smoke E2E con Ollama automatizado (falta acreditar corrida en staging) |
| P2 | CVEs transitivos (chromadb/ragas/npm–Vite/esbuild) |
| P2 | Cookie HttpOnly opcional (activar en HTTPS; Bearer sigue válido) |
| P2 | React Router **v7 aplicado**; residual `esbuild`/Vite 5 |
| P3 | Cola async index/query + sync compat; baseline `/health` OK |

Cierre 2026-11-20: smoke E2E Ollama, HttpOnly flag, cola async, RR v7 — ver `docs/EVALUACION_SESION_HTTPONLY.md`, `docs/COLA_ASYNC.md`, `scripts/smoke_e2e_ollama.py`.

---

## 7. Observaciones

1. Trazabilidad metodológica completa en `docs/00`–`07`.
2. FURPS y OWASP avanzaron en la misma rama `owasp` sin romper arquitectura hexagonal.
3. No se autoriza presentar el sistema como OWASP “completo” ni como asesor oficial.
4. Residual operativo: ensayo restore firmado + `npm audit` residual Vite/`esbuild` (fix force = Vite 8).

---

## 8. Recomendación final

**Apto para producción con observaciones.**

Condiciones mínimas antes de piloto externo:

1. Checklist de producción cumplido.  
2. Backup MySQL + knowledge tomados.  
3. Smoke E2E con MySQL y Ollama.  
4. Al menos un curator configurado si knowledge está en `curators_only`.  

Si no se cumplen, el dictamen degrada a **No apto para producción** (solo lab local).
