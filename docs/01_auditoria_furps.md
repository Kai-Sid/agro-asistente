# 01 — Auditoría FURPS+

| Campo | Valor |
|---|---|
| Proyecto | Agro Asistente (`Kai-Sid/agro-asistente`) |
| Rol | Auditor Senior de Calidad (FURPS+) |
| Fecha | 2026-11-20 |
| Rama / HEAD | `owasp` / `ae106ea` (+ cambios de ejecución del plan maestro) |
| Método | Revisión estática de código, docs y tests; sin asumir funcionalidades inexistentes |
| Entrada | `docs/00_plan_maestro_furps_owasp.md` |

---

## Resumen ejecutivo

Agro Asistente presenta un **PMV1 usable** (auth, contextos, consulta RAG, conocimiento, clima, clasificación/riesgo experimental) con arquitectura hexagonal verificable. La calidad FURPS+ es **parcial**: funcionalidad core presente, UX con brechas, fiabilidad sin atomicidad ni backups documentados, performance sin baseline, supportability sin CI ni docs FURPS versionados (antes de esta corrida).

**Score global orientativo: 63 / 100**  
**Nivel: Cumple parcialmente (apto para piloto académico con observaciones)**

| Dimensión | Peso | Score | Ponderado |
|---|---:|---:|---:|
| Functionality (F) | 25% | 72 | 18.0 |
| Usability (U) | 20% | 62 | 12.4 |
| Reliability (R) | 20% | 55 | 11.0 |
| Performance (P) | 15% | 48 | 7.2 |
| Supportability (S) | 15% | 58 | 8.7 |
| + Design / Implementation | 5% | 78 | 3.9 |
| **Total** | 100% | | **61.2 ≈ 63** (redondeo a escala de informe) |

---

## Functionality (F) — 72/100

### Implementado

| HU / capacidad | Evidencia |
|---|---|
| HU-01 Registro | `auth_controller.py`, `RegisterPage.jsx`, tests register |
| HU-02 Login JWT | `auth_controller.py`, `LoginPage.jsx`, bcrypt + JWT |
| HU-03 Contextos | `context_controller.py`, `ContextPage.jsx`, aislamiento por `agricultor_id` |
| HU-04/06 Consulta RAG | `RegistrarConsulta`, Chroma, Ollama, `QueryPage.jsx` |
| HU-05 Conocimiento | ingest + list; hash duplicados |
| Clima SENAMHI | `weather_controller.py` |
| Clasificación / riesgo | endpoints + docs HU08 (experimental) |

### Parcial / ausente

| Hallazgo | Evidencia | Severidad |
|---|---|---|
| Sin historial `GET /queries` | No hay ruta listado consultas en controllers | Media |
| UI sin indexación Chroma | `client.js` no expone `POST /knowledge/index`; `KnowledgePage.jsx` solo ingest | Media |
| HU-08 no listo para uso agronómico | `docs/HU08_*`; avisos experimentales en UI | Alta (alcance) |
| RAGAS sin puntuaciones oficiales | `README.md`, `backend/evaluation/` | Media |

---

## Usability (U) — 62/100

| Hallazgo | Evidencia | Severidad |
|---|---|---|
| Fallo silencioso al cargar contexto | `QueryPage.jsx` `.catch(() => {})` | Alta |
| Sin ruta 404 SPA | `App.jsx` sin `path="*"` | Media |
| Copy Knowledge desfasado | “Todavía no hay búsqueda semántica ni RAG” mientras query usa RAG | Media |
| Health técnico en Home | `HomePage.jsx` muestra MySQL/fase/arquitectura al usuario final | Baja |
| Feedback positivo | Formularios ES, loading, 429/403 en login/knowledge, `aria-live` en respuesta | — |

---

## Reliability (R) — 55/100

| Hallazgo | Evidencia | Severidad |
|---|---|---|
| Persistencia no atómica consulta/respuesta/evidencias | `registrar_consulta.py` + commits separados en `repositorio_consulta.py` / `repositorio_evidencia.py` | Alta |
| Sin runbook backups/RTO | No hay docs/scripts de backup en repo | Alta |
| 503 controlado si Ollama cae | `query_controller` / generación | Positivo |
| Health con MySQL opcional | `/health` sigue ok si DB cae (detalle según env) | Parcial |

---

## Performance (P) — 48/100

| Hallazgo | Evidencia | Severidad |
|---|---|---|
| Indexación síncrona | `POST /knowledge/index` bloqueante | Media |
| Timeouts largos | Ollama 90s; cliente query 120s | Media |
| Sin baseline p50/p95 | No hay script/métricas en repo | Media |
| Embeddings léxicos locales | Bajo costo vs embeddings neuronales | Positivo relativo |

---

## Supportability (S) — 58/100

| Hallazgo | Evidencia | Severidad |
|---|---|---|
| Hexagonal + tests amplios | `backend/tests/*`, `test_architecture.py` | Positivo |
| Sin CI GitHub Actions | No existe `.github/` | Alta |
| Frontend sin script `test` | `frontend/package.json` | Media |
| `requirements.txt` con rangos | A06 / mantenibilidad | Media |
| Docs FURPS 01–03 ausentes al inicio | Inventario `docs/` | Alta (cerrado en esta fase) |
| Drift nombres EN docs vs ES schema | `ARQUITECTURA.md` vs `schema.sql` | Baja |

---

## + Design / Implementation — 78/100

- Dominio sin FastAPI/SQLAlchemy (puertos/adaptadores).
- Controles OWASP detrás de flags (compatibilidad demos).
- Duplicidad residual de adapters EN (`query_repository.py`) vs ES activos (`repositorio_consulta.py`) — deuda menor si no se cablean.

---

## Riesgos detectados

1. Consulta a medias en BD si falla el commit de evidencias.
2. Piloto sin procedimiento de restauración.
3. UX oculta errores de contexto → consultas fallidas confusas.
4. Sin CI → regresiones no detectadas en PRs.
5. Indexación solo por API/curl → operadores no curadores sin UI clara.

---

## Recomendaciones de alto nivel

1. Publicar plan `02` e implementar M02 (backups), U01 (UX), M08 (atomicidad), S01 (CI/test script), F01 (index UI).
2. Registrar baseline de performance (P01) aunque sea lab.
3. Ejecutar suite con MySQL y documentar resultados sin inventar verdes.
4. Mantener flags OWASP compatibles; no mezclar endurecimiento prod con demos locales.
