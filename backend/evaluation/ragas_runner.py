from __future__ import annotations

import asyncio
import math
import os
from dataclasses import dataclass

from app.infrastructure.config.settings import Settings
from evaluation.pipeline import MuestraPipeline, filas_ragas
from evaluation.preflight import (
    EvaluacionOficialNoEjecutable,
    exigir_modelo_embeddings_ragas,
    proveedor_juez_ragas,
)

DEFAULT_OLLAMA_EMBEDDING_MODEL = "nomic-embed-text"
METRIC_NAMES = ("faithfulness", "context_recall", "answer_relevancy")


@dataclass(frozen=True)
class ConfiguracionRagas:
    metric_names: tuple[str, ...]
    llm_provider: str
    llm_model: str
    embedding_model: str
    requires_openai_key: bool
    notes: tuple[str, ...]


def describir_configuracion(settings: Settings) -> ConfiguracionRagas:
    proveedor = proveedor_juez_ragas()
    notas = [
        "Métricas modernas de ragas==0.4.3 (collections): Faithfulness, ContextRecall, AnswerRelevancy.",
        "No se mezcla con la API legacy de ragas.metrics ni con LangchainEmbeddingsWrapper.",
        "El juez RAGAS no vive en domain/application.",
    ]
    if proveedor == "openai":
        return ConfiguracionRagas(
            metric_names=METRIC_NAMES,
            llm_provider="openai",
            llm_model=os.environ.get("RAGAS_OPENAI_MODEL") or "gpt-4o-mini",
            embedding_model=os.environ.get("RAGAS_EMBEDDING_MODEL") or "text-embedding-3-small",
            requires_openai_key=True,
            notes=tuple(
                notas
                + [
                    "RAGAS_LLM_PROVIDER=openai usa OPENAI_API_KEY (no versionar la clave).",
                ]
            ),
        )
    return ConfiguracionRagas(
        metric_names=METRIC_NAMES,
        llm_provider="ollama",
        llm_model=settings.ollama_model,
        embedding_model=(
            os.environ.get("RAGAS_EMBEDDING_MODEL") or DEFAULT_OLLAMA_EMBEDDING_MODEL
        ).strip(),
        requires_openai_key=False,
        notes=tuple(
            notas
            + [
                "Juez local vía API compatible OpenAI de Ollama (OLLAMA_BASE_URL/v1).",
                "AnswerRelevancy exige un modelo de embeddings Ollama (por defecto nomic-embed-text).",
                "Instalar con: ollama pull nomic-embed-text",
                "No usar qwen2.5:1.5b como embedding: no expone la capacidad de embeddings.",
            ]
        ),
    )


def exigir_configuracion_juez(settings: Settings) -> ConfiguracionRagas:
    config = describir_configuracion(settings)
    if config.requires_openai_key and not (os.environ.get("OPENAI_API_KEY") or "").strip():
        raise EvaluacionOficialNoEjecutable(
            "EVALUACIÓN OFICIAL DETENIDA: RAGAS_LLM_PROVIDER=openai pero falta OPENAI_API_KEY. "
            "No se colocan claves en el código. Use el juez Ollama (valor por defecto) "
            "o exporta OPENAI_API_KEY en el entorno."
        )
    if config.llm_provider == "ollama":
        exigir_modelo_embeddings_ragas(settings, config.embedding_model)
    return config


def ejecutar_ragas(muestras: list[MuestraPipeline], settings: Settings) -> dict[str, object]:
    config = exigir_configuracion_juez(settings)
    from evaluation.ragas_compat import aplicar_compatibilidad_langchain

    aplicar_compatibilidad_langchain()
    scores = asyncio.run(_evaluar_colecciones(muestras, settings, config))
    _exigir_scores_completos(scores, config)
    scores["configured_metrics"] = list(config.metric_names)
    scores["judge"] = {
        "provider": config.llm_provider,
        "model": config.llm_model,
        "embedding_model": config.embedding_model,
        "api": "ragas.metrics.collections",
    }
    return scores


async def _evaluar_colecciones(
    muestras: list[MuestraPipeline],
    settings: Settings,
    config: ConfiguracionRagas,
) -> dict[str, object]:
    from ragas.embeddings.base import embedding_factory
    from ragas.llms import llm_factory
    from ragas.metrics.collections import AnswerRelevancy, ContextRecall, Faithfulness

    client = _cliente_async(settings, config)
    llm = llm_factory(config.llm_model, client=client)
    embeddings = embedding_factory(
        provider="openai",
        model=config.embedding_model,
        client=client,
    )
    faithfulness = Faithfulness(llm=llm)
    context_recall = ContextRecall(llm=llm)
    answer_relevancy = AnswerRelevancy(llm=llm, embeddings=embeddings)

    rows: list[dict[str, float | None]] = []
    for fila in filas_ragas(muestras):
        user_input = str(fila["user_input"])
        response = str(fila["response"])
        contexts = list(fila["retrieved_contexts"])
        reference = str(fila["reference"])
        f_score = await faithfulness.ascore(
            user_input=user_input,
            response=response,
            retrieved_contexts=contexts,
        )
        c_score = await context_recall.ascore(
            user_input=user_input,
            retrieved_contexts=contexts,
            reference=reference,
        )
        a_score = await answer_relevancy.ascore(
            user_input=user_input,
            response=response,
        )
        rows.append(
            {
                "faithfulness": _valor_metrica(f_score),
                "context_recall": _valor_metrica(c_score),
                "answer_relevancy": _valor_metrica(a_score),
            }
        )

    averages = {
        name: _promedio([row[name] for row in rows])
        for name in METRIC_NAMES
    }
    return {"averages": averages, "rows": len(rows), "per_sample": rows}


def _valor_metrica(resultado: object) -> float | None:
    value = getattr(resultado, "value", resultado)
    try:
        number = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _promedio(valores: list[float | None]) -> float | None:
    finitos = [valor for valor in valores if valor is not None and math.isfinite(valor)]
    if not finitos or len(finitos) != len(valores):
        return None
    return float(sum(finitos) / len(finitos))


def _exigir_scores_completos(scores: dict[str, object], config: ConfiguracionRagas) -> None:
    averages = scores.get("averages")
    if not isinstance(averages, dict):
        raise EvaluacionOficialNoEjecutable(
            "EVALUACIÓN OFICIAL DETENIDA: RAGAS no devolvió promedios numéricos."
        )
    faltantes: list[str] = []
    for name in config.metric_names:
        value = averages.get(name)
        try:
            number = float(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            faltantes.append(name)
            continue
        if not math.isfinite(number):
            faltantes.append(name)
    if faltantes:
        raise EvaluacionOficialNoEjecutable(
            "EVALUACIÓN OFICIAL DETENIDA: métricas ausentes o NaN: "
            + ", ".join(faltantes)
            + ". La corrida no se considera exitosa."
        )


def _cliente_async(settings: Settings, config: ConfiguracionRagas):
    from openai import AsyncOpenAI

    if config.llm_provider == "openai":
        return AsyncOpenAI()
    base = settings.ollama_base_url.rstrip("/") + "/v1"
    return AsyncOpenAI(
        base_url=base,
        api_key=os.environ.get("RAGAS_OLLAMA_API_KEY") or "ollama",
    )
