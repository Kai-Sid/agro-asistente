# Cadena de suministro (OWASP A06 / R-10)

| Campo | Valor |
|---|---|
| Fecha | 2026-11-20 |
| Lock Python | `backend/requirements.lock.txt` (`pip freeze` del venv de auditoría) |
| Requirements declarativo | `backend/requirements.txt` |

## Cómo instalar de forma reproducible

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.lock.txt
```

Para desarrollo flexible seguir usando `requirements.txt`.

## Auditoría ejecutada

### pip-audit (sobre dependencias resueltas)

Hallazgos conocidos (no se afirman “cero CVE”):

| Paquete | Hallazgos (ids) | Notas |
|---|---|---|
| `chromadb` 1.5.9 | PYSEC-2026-311, 3813, 3814, 3815 | Sin fix versions reportadas en la corrida; residual aceptado para piloto con Chroma local |
| `ragas` 0.4.3 | PYSEC-2026-3046 | Solo evaluación; fuera del path de negocio |
| `diskcache` 5.6.3 | PYSEC-2026-2447 | Transitiva |
| `langchain-openai` 1.1.9 | PYSEC-2026-76 | Fix sugerido 1.1.14; dependencia de RAGAS, no del API |

**Acción piloto:** documentar residual; no forzar upgrades masivos que rompan RAGAS/Chroma en la misma fase. Re-auditar en el siguiente sprint.

### npm audit (frontend)

Corrida actualizada 2026-11-20 (post upgrade **React Router v7** + `axios@1.13.2` + `vite@5.4.21`):

| Ámbito | Severidad | Nota |
|---|---|---|
| `esbuild` vía `vite` | moderate | Persistente en advisory pese a Vite 5.4.21; residual (Vite 6 es breaking mayor) |
| `react-router` / `react-router-dom` | — | **Migrado a v7** (APIs `BrowserRouter`/`Routes` conservadas) |
| `follow-redirects` / `source-map-js` | — | Mitigados vía `npm audit fix` / upgrade axios |

Residual A06 frontend: `esbuild`/`vite` (advisory GHSA-67mh-4wv8-2f99). Fix force → Vite 8 (breaking); **no aplicado** en PMV1. React Router v7 **aplicado** (build + tests OK).

## CI

El workflow `.github/workflows/ci.yml` instala desde `requirements.txt`. Evolución recomendada: job opcional `pip-audit` / `npm audit` con `continue-on-error` hasta limpiar CVEs transitivos.
