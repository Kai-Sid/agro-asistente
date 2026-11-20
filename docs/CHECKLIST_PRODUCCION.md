# Checklist de producción / piloto endurecido

Usar antes de exponer el API fuera de un laboratorio controlado.

## Variables obligatorias

| Variable | Valor esperado |
|---|---|
| `APP_ENV` | `production` |
| `JWT_SECRET` | ≥ 32 caracteres, no el default |
| `CORS_ORIGINS` | Orígenes exactos HTTPS (sin `*`) |
| `MYSQL_*` | Credenciales reales |

## Controles OWASP recomendados

| Variable | Valor |
|---|---|
| `KNOWLEDGE_MUTATION_POLICY` | `curators_only` |
| `KNOWLEDGE_CURATOR_EMAILS` | Correos curator separados por coma |
| `PASSWORD_POLICY` | `strong` |
| `WEATHER_REQUIRE_AUTH` | `true` |
| `RATE_LIMIT_ENABLED` | `true` |
| `MODEL_INTEGRITY_CHECK` | `true` |
| `PROMPT_HARDENING` | `true` |
| `SECURITY_LOG_ENABLED` | `true` |
| `URL_ALLOWLIST_ENFORCE` | `true` (o confiar en default prod) |

## Frontend

| Variable | Valor |
|---|---|
| `VITE_API_BASE_URL` | URL HTTPS del API sin barra final |
| `VITE_AUTH_STORAGE` | `session` (o vacío: el build PROD ya usa session) |

## Verificaciones go / no-go

1. Arranque con `APP_ENV=production` y `JWT_SECRET` débil → **debe fallar**.
2. Arranque con secreto fuerte → `/health` responde sin OpenAPI (`/docs` 404).
3. Farmer no curator + `curators_only` → ingest/index **403**.
4. Login ráfaga → **429** con rate limit activo.
5. Backup MySQL + `knowledge/` según `RUNBOOK_BACKUP.md`.
6. Smoke: register → login → context → query → knowledge list.

## Render

Completar en el panel los secretos `sync: false` del `render.yaml` y las variables de endurecimiento listadas arriba. El blueprint no crea MySQL ni Ollama.
