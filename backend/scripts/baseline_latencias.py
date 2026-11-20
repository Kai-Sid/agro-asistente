"""Baseline de latencias (FURPS P01) para endpoints críticos.

Uso (API local levantada):

    python scripts/baseline_latencias.py --base-url http://127.0.0.1:8000

Sin token JWT solo mide /health. Con --token mide /api/v1/contexts.
No inventa resultados: imprime mediciones o SKIP.
"""

from __future__ import annotations

import argparse
import statistics
import time
import urllib.error
import urllib.request


def _medir(url: str, headers: dict[str, str] | None = None, repeats: int = 5) -> list[float]:
    tiempos: list[float] = []
    for _ in range(repeats):
        request = urllib.request.Request(url, headers=headers or {})
        inicio = time.perf_counter()
        with urllib.request.urlopen(request, timeout=30) as response:
            response.read()
            if response.status >= 400:
                raise RuntimeError(f"HTTP {response.status} en {url}")
        tiempos.append((time.perf_counter() - inicio) * 1000)
    return tiempos


def _resumen(nombre: str, muestras: list[float]) -> None:
    orden = sorted(muestras)
    p50 = statistics.median(orden)
    idx95 = min(len(orden) - 1, max(0, int(round(0.95 * (len(orden) - 1)))))
    p95 = orden[idx95]
    print(f"{nombre}: n={len(orden)} p50={p50:.1f}ms p95={p95:.1f}ms max={max(orden):.1f}ms")


def main() -> int:
    parser = argparse.ArgumentParser(description="Baseline latencias Agro Asistente")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--token", default="", help="JWT Bearer opcional")
    parser.add_argument("--repeats", type=int, default=5)
    args = parser.parse_args()
    base = args.base_url.rstrip("/")

    print("Umbrales piloto orientativos: /health p95 < 500ms; /contexts p95 < 1000ms")
    try:
        _resumen("GET /health", _medir(f"{base}/health", repeats=args.repeats))
    except (urllib.error.URLError, TimeoutError, RuntimeError) as error:
        print(f"GET /health: SKIP ({error})")
        return 1

    if args.token.strip():
        headers = {"Authorization": f"Bearer {args.token.strip()}"}
        try:
            _resumen(
                "GET /api/v1/contexts",
                _medir(f"{base}/api/v1/contexts", headers=headers, repeats=args.repeats),
            )
        except (urllib.error.URLError, TimeoutError, RuntimeError) as error:
            print(f"GET /api/v1/contexts: SKIP ({error})")
    else:
        print("GET /api/v1/contexts: SKIP (sin --token)")

    print("GET /api/v1/queries (POST RAG/Ollama): no medido aquí (costoso/no determinista).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
