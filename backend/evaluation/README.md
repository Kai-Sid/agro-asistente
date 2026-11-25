# Evaluación RAGAS — línea base PMV1

## Propósito

Establecer la **primera línea base** del PMV1:

pregunta agrícola → RAG (Chroma + embeddings léxicos) → Ollama / Qwen2.5 (tag en `OLLAMA_MODEL`) → RAGAS.

No hay fine-tuning ni LoRA. RAGAS es una **herramienta de evaluación**, no parte del dominio ni de la aplicación.

## Dataset

Archivo: `evaluation/data/pmv1_baseline.json`

- 6 preguntas
- `ground_truth` copiado de `knowledge/prueba-riego-papa.md` y `knowledge/prueba-heladas-sierra.md`
- cada item declara `source_documents`

No se inventó agronomía fuera de esos Markdown.

## Métricas (ragas 0.4.3, API moderna `collections`)

| Dimensión | Clase RAGAS | Clave en scores |
|---|---|---|
| Fidelidad de la respuesta al contexto | `Faithfulness` | `faithfulness` |
| Calidad de recuperación | `ContextRecall` | `context_recall` |
| Relevancia de la respuesta | `AnswerRelevancy` | `answer_relevancy` |

Se usa únicamente la API moderna (`ragas.metrics.collections` + `embedding_factory`/`llm_factory` con cliente async). No se mezclan wrappers legacy.

El juez por defecto es Ollama (`OLLAMA_BASE_URL/v1`). `AnswerRelevancy` necesita un modelo de **embeddings** aparte (`RAGAS_EMBEDDING_MODEL=nomic-embed-text`). No usar `qwen2.5:1.5b` como embedding.

```powershell
ollama pull nomic-embed-text
```

Alternativa de juez: `RAGAS_LLM_PROVIDER=openai` + `OPENAI_API_KEY` (nunca en el repositorio).

Una corrida con métricas ausentes/NaN o sin persistencia MySQL **no** se considera exitosa (exit code 2).

## Requisitos para la corrida oficial

1. `pip install -r requirements.txt` (incluye `ragas==0.4.3`)
2. `GENERATION_PROVIDER=ollama` (si vale `template`, el script **se detiene**)
3. Ollama en ejecución, `ollama pull` del tag en `OLLAMA_MODEL` y `ollama pull nomic-embed-text`
4. Colección Chroma `agro_knowledge_pmv1` **con documentos indexados**
5. Ejecutar desde `backend/`

MySQL no interviene en la puntuación RAGAS. Sí hace falta para **indexar** conocimiento si Chroma está vacío (`POST /api/v1/knowledge/index`).

## Comando

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m evaluation.run_baseline
```

Salida: `evaluation/results/pmv1_baseline_samples_<UTC>.json` y `pmv1_baseline_scores_<UTC>.json`.

## Estado

Ver `RESULTADOS_PENDIENTES.md`. **No hay puntuaciones inventadas.**

## Google Colab Pro

Notebook opcional: `evaluation/ragas_baseline.ipynb`. Usa el mismo dataset. **No se afirma que se haya ejecutado en Colab.**

## Matriz de evidencia

| Herramienta | Uso en PMV1 | Estado |
|---|---|---|
| RAGAS | Evaluación de línea base | Preparado (`ragas==0.4.3`); corrida real pendiente |
| Ollama | Generación del PMV1 y juez RAGAS por defecto | Requisito de la corrida oficial |
| Qwen2.5 1.8B | SLM base (tag Ollama configurable; default `qwen2.5:1.5b`) | Configurado, no ejecutado aquí |
| Python | Script `evaluation.run_baseline` | Preparado |
| Google Colab Pro | Ejecución opcional del notebook | Notebook creado; no ejecutado |
