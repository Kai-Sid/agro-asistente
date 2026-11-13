# Remediaciones OWASP aplicadas

Resumen de lo implementado según `docs/05_plan_owasp.md`. Compatibilidad hacia atrás mediante flags (defaults seguros para demos locales).

| ID | Control | Estado |
|---|---|---|
| R-01 | `JWT_SECRET` enforce en producción / warning en desarrollo | Aplicado |
| R-02 | Logging `agro.security` (login, register, 401, ingest, rate limit) | Aplicado |
| R-03 | Rate limit login/register (y consultas) | Aplicado |
| R-04 | OpenAPI off en production; health mínimo en production | Aplicado |
| R-05 | `KNOWLEDGE_MUTATION_POLICY` + rol JWT `farmer`/`curator` | Aplicado |
| R-06 | `PASSWORD_POLICY=basic\|strong` | Aplicado |
| R-07 | `WEATHER_REQUIRE_AUTH` + allowlist URLs en production | Aplicado |
| R-08 | Prompt hardening (delimitadores + patrones) | Aplicado |
| R-09 | SHA-256 de modelos `.joblib` (enforce en production) | Aplicado |
| R-10 | Documentado; lock Python pendiente de proceso CI | Parcial |
| R-11 | `VITE_AUTH_STORAGE` + CSP básica en `index.html` | Parcial (sin cookies HttpOnly aún) |
| R-12 | CORS métodos/headers explícitos | Aplicado |
| R-13 | Cuota suave en `/queries` | Aplicado |

## Validaciones mínimas cubiertas en tests

Archivo: `backend/tests/test_security_owasp.py`

- Inicio de sesión / JWT con `role` y `exp`
- Gestión de sesiones (401 sin token; APIs con Bearer)
- APIs protegidas (contextos)
- Roles y permisos (`curators_only` → 403 en ingest; GET documents OK)
- Formularios (password corta / policy strong)
- Integraciones (ruta weather viva; integridad de modelo; prompt hardening)

Las pruebas que persisten en MySQL requieren el servidor de base de datos en marcha.
