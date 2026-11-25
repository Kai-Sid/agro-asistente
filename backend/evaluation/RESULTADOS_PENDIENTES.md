# RESULTADOS RAGAS — estado PMV3

## Corrida aceptada (2026-11-25)

Archivos locales (gitignored `*.json` en `results/`):

- `pmv3-evaluation-v1_samples_20261125T054127Z.json`
- `pmv3-evaluation-v1_scores_20261125T054127Z.json`
- MySQL `evaluaciones_ia.id = 1` + detalles

Juez: Ollama `qwen2.5:1.5b` · embeddings: `nomic-embed-text` · API: `ragas.metrics.collections`

Los proxies léxicos (`retrieval_precision_lexical_proxy`, `answer_pertinence_lexical_coverage`) **no** son validación agronómica.

## Corrida histórica incompleta (no aprobar)

Ver `results/INCOMPLETE_20261125T051444Z.md` (`answer_relevancy=NaN`, fallo MySQL).

## Cómo ejecutar

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
# Requisitos: ollama pull qwen2.5:1.5b ; ollama pull nomic-embed-text
$env:RAGAS_EMBEDDING_MODEL='nomic-embed-text'
python -m evaluation.run_baseline
```

Una corrida con métricas NaN/ausentes o sin persistencia MySQL termina con código 2 y **no** se considera exitosa.

## Variables

| Variable | Rol |
|---|---|
| `GENERATION_PROVIDER` | Debe ser `ollama` |
| `OLLAMA_BASE_URL` | p. ej. `http://127.0.0.1:11434` |
| `OLLAMA_MODEL` | Tag de chat (default `qwen2.5:1.5b`) |
| `RAGAS_EMBEDDING_MODEL` | Embeddings del juez (`nomic-embed-text`) |
| `RAGAS_LLM_PROVIDER` | `ollama` (defecto) u `openai` |
| `OPENAI_API_KEY` | Solo si el juez es OpenAI |
