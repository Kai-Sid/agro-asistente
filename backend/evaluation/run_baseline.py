"""Ejecuta y persiste la evaluación RAGAS. Ejecutar desde backend/: python -m evaluation.run_baseline"""

from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

from app.infrastructure.adapters.output.mysql.connection import create_session_factory
from app.infrastructure.adapters.output.mysql.procedures import MysqlStoredProcedureGateway
from app.infrastructure.config.settings import Settings, get_settings
from evaluation.dataset import cargar_dataset
from evaluation.pipeline import (
    construir_generacion,
    construir_recuperacion,
    ejecutar_dataset,
    exigir_indice_chroma,
    filas_ragas,
    pertinencia_lexica,
    precision_recuperacion_lexica,
)
from evaluation.preflight import EvaluacionOficialNoEjecutable, exigir_ollama_disponible
from evaluation.ragas_runner import describir_configuracion, ejecutar_ragas

RESULTS_DIR = Path(__file__).resolve().parent / "results"


def main() -> int:
    settings = _settings_de_evaluacion()
    try:
        exigir_ollama_disponible(settings)
        recuperacion = construir_recuperacion(settings)
        exigir_indice_chroma(recuperacion)
        generacion = construir_generacion(settings)
        dataset_path = Path(settings.evaluation_dataset_path) if settings.evaluation_dataset_path else None
        dataset = cargar_dataset(dataset_path)
        muestras = ejecutar_dataset(dataset, recuperacion, generacion)
        scores = ejecutar_ragas(muestras, settings)
    except EvaluacionOficialNoEjecutable as error:
        print(str(error), file=sys.stderr)
        return 2

    precision_values = [precision_recuperacion_lexica(item) for item in muestras]
    pertinencia_values = [pertinencia_lexica(item) for item in muestras]
    average_duration = _promedio([item.duration_ms for item in muestras])
    averages = scores.get("averages", {})
    faithfulness = _metric(averages, "faithfulness")
    context_recall = _metric(averages, "llm_context_recall")
    response_relevancy = _metric(averages, "answer_relevancy")
    scores["pmv3_metrics"] = {
        "retrieval_precision_lexical_proxy": _promedio(precision_values),
        "answer_pertinence_lexical_coverage": _promedio(pertinencia_values),
        "average_response_ms": average_duration,
        "interpretation": "Los dos indicadores léxicos son proxies automáticos; RAGAS no sustituye validación agronómica.",
    }

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    slug = "".join(char if char.isalnum() or char in "-_" else "_" for char in dataset.id)
    samples_path = RESULTS_DIR / f"{slug}_samples_{stamp}.json"
    scores_path = RESULTS_DIR / f"{slug}_scores_{stamp}.json"
    payload_samples = {
        "dataset_id": dataset.id,
        "dataset_version": dataset.phase,
        "generated_at": stamp,
        "generation_provider": settings.generation_provider,
        "ollama_model": settings.ollama_model,
        "samples": [
            {
                "id": item.id,
                "question": item.question,
                "answer": item.answer,
                "contexts": item.contexts,
                "ground_truth": item.ground_truth,
                "source_documents": item.source_documents,
                "generation_method": item.generation_method,
                "response_time_ms": item.duration_ms,
                "retrieval_precision_lexical_proxy": precision_recuperacion_lexica(item),
                "answer_pertinence_lexical_coverage": pertinencia_lexica(item),
            }
            for item in muestras
        ],
        "ragas_rows": filas_ragas(muestras),
    }
    samples_path.write_text(json.dumps(payload_samples, ensure_ascii=False, indent=2), encoding="utf-8")
    scores_path.write_text(json.dumps(scores, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Muestras reales: {samples_path}")
    print(f"Puntuaciones RAGAS: {scores_path}")
    print(json.dumps(scores, ensure_ascii=False, indent=2))

    try:
        evaluation_id = _guardar_en_mysql(
            settings=settings,
            dataset_version=dataset.id,
            muestras=muestras,
            precision_promedio=_promedio(precision_values),
            pertinencia_promedio=_promedio(pertinencia_values),
            fidelidad=faithfulness,
            recall_contexto=context_recall,
            duracion_promedio_ms=average_duration,
        )
        print(f"Evaluación guardada en MySQL: {evaluation_id}")
    except Exception as error:
        print(
            "ADVERTENCIA: se guardaron los archivos JSON, pero no se pudo registrar la evaluación en MySQL: "
            + str(error),
            file=sys.stderr,
        )
    return 0


def _guardar_en_mysql(
    settings: Settings,
    dataset_version: str,
    muestras: list,
    precision_promedio: float,
    pertinencia_promedio: float,
    fidelidad: float | None,
    recall_contexto: float | None,
    duracion_promedio_ms: float,
) -> str:
    gateway = MysqlStoredProcedureGateway(create_session_factory(settings))
    headers = gateway.call(
        "sp_evaluacion_ia_guardar",
        (
            dataset_version[:100],
            settings.generation_provider[:40],
            settings.ollama_model[:120],
            precision_promedio,
            pertinencia_promedio,
            fidelidad,
            recall_contexto,
            duracion_promedio,
            len(muestras),
        ),
    )
    if not headers:
        raise RuntimeError("El procedimiento no devolvió el identificador de evaluación")
    evaluation_id = str(headers[0]["id"])
    for item in muestras:
        gateway.call(
            "sp_evaluacion_ia_detalle_guardar",
            (
                int(evaluation_id),
                item.id[:100],
                item.question,
                precision_recuperacion_lexica(item),
                pertinencia_lexica(item),
                item.duration_ms,
                item.answer,
            ),
        )
    return evaluation_id


def _promedio(values: list[float]) -> float:
    return round(sum(values) / len(values), 6) if values else 0.0


def _metric(averages: object, key: str) -> float | None:
    if not isinstance(averages, dict):
        return None
    try:
        value = float(averages.get(key))
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def _settings_de_evaluacion() -> Settings:
    get_settings.cache_clear()
    return get_settings()


if __name__ == "__main__":
    config = describir_configuracion(_settings_de_evaluacion())
    print("Configuración RAGAS prevista:", flush=True)
    print(f"  juez={config.llm_provider} modelo={config.llm_model}", flush=True)
    print(f"  métricas={', '.join(config.metric_names)}", flush=True)
    sys.exit(main())
