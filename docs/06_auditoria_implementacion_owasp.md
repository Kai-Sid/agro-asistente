# 06 — Auditoría de implementación OWASP Top 10

| Campo | Valor |
|---|---|
| Proyecto | `Kai-Sid/agro-asistente` |
| Rol | Auditor Independiente de Seguridad |
| Entradas | `04_auditoria_owasp.md`, `05_plan_owasp.md`, código actual |
| Fecha | 2026-11-20 |
| Método | Revisión estática + pytest selectivo + npm/pip audit |

---

## Resumen ejecutivo

| Indicador | Valor |
|---|---|
| Score inicial (04 histórico) | 38 / 100 |
| Score post R-01…R-13 (06 anterior) | 60 / 100 |
| **Score actual (delta 2026-11-20)** | **68 / 100** |
| Variación vs 60 | **+8** |
| Nivel | **Aceptable con reservas** para piloto endurecido; insuficiente si se dejan defaults demo |

| Estado categorías | Cantidad |
|---|---:|
| Corregida | 1 (A09) |
| Parcialmente corregida | **9** |
| No corregida | **0** |

---

## Evidencia de pruebas (esta corrida)

```text
frontend: npm test → 23 passed (incluye test session PROD)
backend: pytest unitarios clave → 46+ passed
backend: test_security_owasp.py (con MySQL XAMPP + schema) → 14 passed
         (incluye login/JWT role, contextos con token, roles curator)
pip-audit → 11 hallazgos en 4 paquetes (documentados en SUPPLY_CHAIN.md)
npm audit → 6 vulnerabilidades (documentadas; sin upgrade forzado)
```

Evidencia dinámica de seguridad con MySQL: **verde**. Smoke E2E con Ollama no forma parte de esta suite.

---

## Veredicto por categoría

### A01 — Broken Access Control — Parcial

- Controles: ownership contextos; `curators_only`; `WEATHER_REQUIRE_AUTH`.
- Residual: defaults demo `open` / weather público si no se usa checklist.
- Delta: checklist + Render `curators_only`; test roles con MySQL **14 passed** en suite seguridad.

### A02 — Cryptographic Failures — Parcial

- Controles: bcrypt; JWT enforce prod; **sessionStorage por defecto en PROD**.
- Residual: sin cookies HttpOnly; secret débil posible si `APP_ENV!=production`.

### A03 — Injection — Parcial

- ORM + Pydantic + `prompt_hardening`.
- Residual: prompt/RAG poisoning.

### A04 — Insecure Design — Parcial

- Rate limits, roles opcionales, cuotas query.
- Residual: registro abierto; knowledge global compartido.

### A05 — Security Misconfiguration — Parcial (mejorado)

- OpenAPI off / health mínimo en prod.
- Delta: `render.yaml` + `CHECKLIST_PRODUCCION.md`.

### A06 — Vulnerable Components — **Parcial** (antes no corregida)

- Delta: `requirements.lock.txt`, rangos acotados, `SUPPLY_CHAIN.md`, auditorías ejecutadas.
- Residual: CVEs en chromadb/ragas/transitivas y 6 npm sin upgrade aplicado.

### A07 — Authentication Failures — Parcial

- Rate limit login/register; password policy; role en JWT.
- Residual: `basic` por defecto en local; sin refresh/denylist.

### A08 — Integrity — Parcial

- SHA-256 joblib + flag.
- Residual: solo artefactos joblib cubiertos.

### A09 — Logging — Corregida (aplicación)

- Logger `agro.security`.
- Residual: sin SIEM externo.

### A10 — SSRF — Parcial

- Allowlist SENAMHI/Ollama en prod.
- Residual: enforce ligado a entorno.

---

## Estado del plan (base + delta)

| ID | Estado |
|---|---|
| R-01…R-09, R-12, R-13 | Aplicados (flags) |
| R-10 | **Parcial** — lock + audit + doc; CVEs residuales |
| R-11 | **Parcial** — session PROD; sin HttpOnly |
| O-CFG | Aplicado (docs + render) |
| O-A01 | Aplicado (ops/docs + evidencia dinámica MySQL 14 passed) |

---

## Riesgos residuales

1. Defaults demo si no se usa checklist.
2. CVEs transitivos Python/npm.
3. XSS aún relevante (CSP + session mitigan, no eliminan).
4. Smoke E2E Ollama / restore backup pendientes.

## Conclusión

Score **68/100** (con MySQL de seguridad en verde). OWASP Top 10 **cumple parcialmente**. Condición para acercarse a ≥70 operativo: activar checklist de producción completo + plan de upgrades de deps en siguiente sprint.
