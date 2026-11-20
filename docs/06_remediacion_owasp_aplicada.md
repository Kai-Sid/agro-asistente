# Remediaciones OWASP aplicadas

Resumen según `docs/05_plan_owasp.md`. Compatibilidad hacia atrás mediante flags.

| ID | Control | Estado |
|---|---|---|
| R-01 | `JWT_SECRET` enforce en producción / warning en desarrollo | Aplicado |
| R-02 | Logging `agro.security` | Aplicado |
| R-03 | Rate limit login/register/queries | Aplicado |
| R-04 | OpenAPI off en production; health mínimo | Aplicado |
| R-05 | `KNOWLEDGE_MUTATION_POLICY` + rol JWT | Aplicado |
| R-06 | `PASSWORD_POLICY=basic\|strong` | Aplicado |
| R-07 | `WEATHER_REQUIRE_AUTH` + allowlist URLs | Aplicado |
| R-08 | Prompt hardening | Aplicado |
| R-09 | SHA-256 modelos `.joblib` | Aplicado |
| R-10 | Lock Python + rangos + `SUPPLY_CHAIN.md` + audits | Parcial (CVEs residuales) |
| R-11 | `sessionStorage` en PROD + `VITE_AUTH_STORAGE` + CSP | Parcial (sin HttpOnly) |
| R-12 | CORS métodos/headers explícitos | Aplicado |
| R-13 | Cuota suave en `/queries` | Aplicado |
| O-CFG | `render.yaml` harden + `CHECKLIST_PRODUCCION.md` | Aplicado |

## Validaciones

- `backend/tests/test_security_owasp.py` (requiere MySQL para login/roles/API).
- Frontend: test de política PROD session en `baseUrl.test.js`.
- Supply chain: `docs/SUPPLY_CHAIN.md`.
