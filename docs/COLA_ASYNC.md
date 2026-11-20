# Cola asíncrona (indexación / consultas largas)

| Campo | Valor |
|---|---|
| Fecha | 2026-11-20 |
| Implementación | En memoria (`JobQueue` + hilo daemon) |
| Persistencia | Solo proceso; se pierde al reiniciar |

## Endpoints

| Método | Ruta | Código | Notas |
|---|---|---|---|
| POST | `/api/v1/knowledge/index` | 200 | Sync (compat) |
| POST | `/api/v1/knowledge/index/async` | 202 | `{ job_id, status, job_type }` |
| POST | `/api/v1/queries` | 201 | Sync (compat) |
| POST | `/api/v1/queries/async` | 202 | Consultas largas (Ollama) |
| GET | `/api/v1/jobs/{job_id}` | 200 | Estado / resultado / error |

Flag: `ASYNC_JOBS_ENABLED=true` (default). Con `false` → 503 en rutas async.

## Rollback

1. `ASYNC_JOBS_ENABLED=false`
2. Clientes usan solo rutas síncronas existentes.
3. No hay migración de datos.

## Límites PMV1

Sin Redis/Celery. Adecuado para piloto local / un worker. No compartir estado entre réplicas.
