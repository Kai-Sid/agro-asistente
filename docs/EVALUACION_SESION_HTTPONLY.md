# Evaluación de sesión HttpOnly (OWASP A02 / A07)

| Campo | Valor |
|---|---|
| Fecha | 2026-11-20 |
| Estado | Implementado detrás de flag (compat PMV1) |
| Cookie | `agro_access_token` |

## Decisión

| Opción | Pros | Contras | Decisión |
|---|---|---|---|
| Solo Bearer en `localStorage`/`sessionStorage` | Simple; SPA actual | XSS puede leer el JWT | Default **compat** (`AUTH_COOKIE_ENABLED=false`) |
| Cookie **HttpOnly** + SameSite | JS no lee el token; mitiga XSS de robo de sesión | CSRF potencial; requiere CORS credentials + Secure en HTTPS | **Piloto / PROD** con flag |
| Híbrido (cookie + body JWT) | Migración gradual; clientes legacy siguen con Bearer | Doble superficie hasta apagar storage | **Implementado** |

## Comportamiento

1. `AUTH_COOKIE_ENABLED=false` (default): login **no** setea cookie; auth solo Bearer (como antes).
2. `AUTH_COOKIE_ENABLED=true`: login setea cookie HttpOnly; Bearer en body **sigue válido**.
3. `POST /api/v1/auth/logout` limpia la cookie.
4. Frontend: `withCredentials: true`; opcional `VITE_AUTH_COOKIE_MODE=true` evita guardar JWT en storage.

## Variables

```env
AUTH_COOKIE_ENABLED=true
AUTH_COOKIE_SECURE=true          # obligatorio en HTTPS / producción
AUTH_COOKIE_SAMESITE=lax         # lax|strict|none (none exige Secure)
```

## Riesgos residuales

- CSRF: mitigado con SameSite=Lax/Strict y orígenes CORS acotados; no hay mutaciones GET.
- XSS: la cookie HttpOnly no es legible por JS; metadatos de UI (nombre) siguen en storage.
- Sin Redis/session store: el JWT sigue siendo stateless; logout solo borra cookie cliente.

## Validación

```powershell
# Tests unitarios (no requieren flag en .env)
cd backend
pytest tests/test_auth_cookie.py -q
```
