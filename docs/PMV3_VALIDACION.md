# Validación ejecutable PMV3

Fecha de actualización: 2026-11-25 (incluye HU-17 simulada)
Entorno: Laragon local · API predeterminada `http://127.0.0.1:8000` (corridas de evidencia de este cierre: `8010` local) · Ollama `127.0.0.1:11434`
Evidencia: `docs/evidencia_pmv3/` · Resultados RAGAS: `backend/evaluation/results/`

## Cierre técnico

| Comprobación | Resultado |
|---|---|
| `GET /health` | **200**, `phase: "3"`, `mysql: "connected"` |
| Procedimientos PMV3 | Instalados (admin, métricas, evaluación) |
| Ollama | Disponible; modelos `qwen2.5:1.5b` y `nomic-embed-text` |
| SQL CRUD directo en Python | No añadido; persistencia vía `MysqlStoredProcedureGateway.callproc` |
| Corrida incompleta previa | Conservada como histórica; **no** es resultado final |

---

## Resumen por historia

| Historia | Estado |
|---|---|
| HU-13 Administración de documentos | **Aprobada en esta corrida** |
| HU-14 Seguridad por roles | **Aprobada** |
| HU-15 Indicadores | **Aprobada en esta corrida** |
| HU-16 Evaluación de IA | **Aprobada en esta corrida** (métricas finitas + MySQL) |
| HU-17 Usabilidad | **Cerrada en simulación sintética** — **pendiente** prueba con personas reales |

---

## HU-13 — Administración de documentos

Evidencia: `docs/evidencia_pmv3/api_validacion_20261125T053755Z.json` (FAILED 0)

| Criterio | Resultado |
|---|---|
| Documento registrado | OK (201, indexado) |
| Edición → versión++ y reindexación | OK (`version: 2`, contenido “extractos botanicos” recuperable) |
| Desactivar permanece en admin | OK (`INACTIVO`) |
| Desactivar no aporta fragmentos | OK |
| Reactivar vuelve a indexarse | OK (documento reaparece en `evidences`) |

### Nota sobre el check de marcador único

La corrida anterior fallaba `hu13_inactive_not_in_retrieval_unique_marker` porque el marcador iba en el campo `text` (eco de la pregunta) y a veces en `answer`. **No** estaba en `evidences` del documento desactivado.

La validación ahora inspecciona solo `evidences` / `document_id`:

- `marker_in_evidences: false`
- `inactive_doc_in_evidences: false`

Motivo documentado en el propio JSON de evidencia (`rationale`).

---

## HU-14 — Seguridad por roles

Sin cambios respecto a la aprobación previa:

| Caso | Resultado |
|---|---|
| Sin token | **401** |
| Token agricultor en rutas admin | **403** |
| Token administrador | **200** |
| UI agricultor en `/admin/*` | Redirección a panel agricultor |

---

## HU-15 — Indicadores

Tras consultas exitosas con Ollama:

- API `GET /api/v1/admin/metrics?days=1`:
  `total_requests=13`, `queries_attended=8`, `requests_with_error=5`
- Coincide con el registro de métricas del periodo (incluye corridas previas con 503 y la validación actual con 201).
- Estado vacío: implementado en UI cuando `total_requests === 0`; observado vía API en corridas tempranas.

---

## HU-16 — Evaluación de IA

### Corrida histórica incompleta (no aprobar)

`backend/evaluation/results/*_20261125T051444Z.json`
Ver `backend/evaluation/results/INCOMPLETE_20261125T051444Z.md`
Problemas: `answer_relevancy=NaN`, fallo MySQL `duracion_promedio`, embeddings incompatibles.

### Corrida aceptada

Comando:

```powershell
cd backend
$env:RAGAS_EMBEDDING_MODEL='nomic-embed-text'
.\.venv\Scripts\python.exe -m evaluation.run_baseline
```

Resultado: `pmv3-evaluation-v1_*_20261125T054127Z.json`

| Métrica | Valor |
|---|---:|
| faithfulness | 0.9722 |
| context_recall | 0.8333 |
| answer_relevancy | 0.0803 |
| retrieval_precision_lexical_proxy | 0.8333 |
| answer_pertinence_lexical_coverage | 0.4417 |
| average_response_ms | 4851.76 |
| MySQL `evaluaciones_ia.id` | **1** |

Notas:

- API moderna `ragas.metrics.collections` (sin mezclar legacy).
- Embeddings: `nomic-embed-text` (no el modelo de chat).
- Proxies léxicos etiquetados como proxies, no validación agronómica.
- `answer_relevancy` baja es un resultado real del juez local (no NaN); conviene revisión manual de respuestas.

Requisito local documentado: `ollama pull nomic-embed-text`.

---

## HU-17 — Usabilidad

Estado: **prueba simulada con perfiles sintéticos** (`SIM-01`…`SIM-03`) documentada en `docs/PMV3_USABILIDAD.md`.

| Criterio técnico | Resultado simulado |
|---|---|
| Flujos principales con datos sintéticos | Aprobados (registro/login/contexto/consulta) |
| Errores comprensibles y recuperables | Aprobado («Credenciales inválidas»; «Completa este campo.») |
| Móvil ~360 px sin scroll horizontal de página | Aprobado (`scrollWidth=360`) |
| Sin HTTP 500 / errores JS en flujos | No observados |
| Prueba con agricultores/usuarios reales | **Fuera de alcance de este cierre** |

Correcciones aplicadas durante la simulación:

- `frontend/src/pages/QueryPage.jsx` — refetch del contexto seleccionado
- `frontend/src/forms/validacionEsp.js` + formularios Login/Register/Context — mensajes HTML5 en español

Evidencia visual: `docs/evidencia_pmv3/hu17/`.

**No** se afirma validación con personas reales.

---

## Archivos de esta actualización técnica

- `backend/evaluation/ragas_runner.py` — API collections + embeddings Ollama
- `backend/evaluation/preflight.py` — exige modelo de embeddings
- `backend/evaluation/run_baseline.py` — `duracion_promedio_ms`, rechazo NaN, persistencia SP
- `backend/evaluation/README.md`, `.env.example`
- `docs/evidencia_pmv3/run_validacion_pmv3.py` — check HU-13 por evidencias
- `docs/evidencia_pmv3/api_validacion_20261125T053755Z.json`
- `backend/evaluation/results/pmv3-evaluation-v1_*_20261125T054127Z.json`
- `backend/evaluation/results/INCOMPLETE_20261125T051444Z.md`
