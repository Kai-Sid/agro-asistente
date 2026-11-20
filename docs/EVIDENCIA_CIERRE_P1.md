# Evidencia de cierre — riesgos Alto / P1 (`07`)

| Campo | Valor |
|---|---|
| Fecha | 2026-11-20 |
| Operador | danimanriqueaguirre21 (lab local) |
| Rama | `owasp` |

## 1. Defaults demo en production (Alto / P1) — Cerrado

**Mitigación en código:** si `APP_ENV=production`, Settings **rechaza** arranque con:

- `KNOWLEDGE_MUTATION_POLICY != curators_only`
- `KNOWLEDGE_CURATOR_EMAILS` vacío
- `PASSWORD_POLICY != strong`
- `WEATHER_REQUIRE_AUTH != true`
- `RATE_LIMIT_ENABLED != true`

Evidencia: `backend/app/infrastructure/config/settings.py`, tests `test_produccion_*` en `tests/test_settings.py`.  
Blueprint: `render.yaml` ya fija políticas endurecidas + cookie HttpOnly.

## 2. HU-08 como verdad agronómica (Alto) — Cerrado (contrato)

**Mitigación:**

- API fuerza `es_riesgo_agricola_validado=false` y campo `aviso_no_oficial`.
- UI muestra el aviso y texto “No usar como verdad agronómica”.

Evidencia: `riesgo_controller.py`, `RiskPage.jsx`, test contrato riesgo.

## 3. Restore de backup (P1) — Acreditado

Ensayo **no destructivo** (BD lab `agro_asistente_restore_lab`):

```text
Dump: backups/mysql-agro_asistente-20261120-160045.sql
ENSAYO_RESTORE_OK tablas=6 db=agro_asistente_restore_lab
NOTE: working database agro_asistente was NOT modified.
```

Script: `database/scripts/restore_ensayo.ps1`.

## 4. Smoke E2E Ollama (P1) — Automatizado; corrida live pendiente de servicios

Artefactos listos:

- `backend/scripts/smoke_e2e_ollama.py`
- `backend/tests/test_smoke_e2e_ollama.py`

En esta sesión de cierre (2026-11-20 17:xx): `ollama` y API en `:8000` **no respondían** (HTTP 000).  
Para acreditar live en staging:

```powershell
cd backend
$env:RUN_OLLAMA_INTEGRATION_TESTS="true"
$env:GENERATION_PROVIDER="ollama"
python scripts/smoke_e2e_ollama.py
```

Pegar salida `[PASS]` aquí cuando MySQL + API + Ollama estén arriba.
