# 07 — Auditoría final integral

| Campo | Valor |
|---|---|
| Proyecto | Agro Asistente (`Kai-Sid/agro-asistente`) |
| Rol | Auditor Principal de Calidad y Seguridad |
| Fecha | 2026-11-13 |
| Entradas | `03_Auditoria_Implementacion_FURPS.md` (Downloads), `docs/06_auditoria_implementacion_owasp.md`, estado local del workspace |
| Commit base remoto / HEAD registrado | `eaac3da2e9c70ab6678a34a51249b6f2a772247d` |
| Alcance del dictamen | Producto PMV1 + remediaciones OWASP presentes en el workspace local (aún **no** consolidadas en `origin/main`) |

---

## 1. Resumen ejecutivo

Agro Asistente conserva una base funcional de PMV1 (auth, contextos, consultas RAG, conocimiento, clima, clasificación, riesgo) y muestra **mejora de seguridad documentada e implementada en local** (score OWASP **38 → 60/100**). En paralelo, el plan FURPS+ **no está cerrado**: la auditoría 03 acredita que `main` remoto no incorporó las 18 mejoras como avance posterior, y varias brechas de calidad/operación siguen abiertas.

**Dictámenes condensados**

| Dimensión | Veredicto |
|---|---|
| Calidad (FURPS+) | **Cumple parcialmente** |
| Seguridad (OWASP Top 10) | **Cumple parcialmente** |
| Funcionalidad | **Se preservó** la existente, con **riesgos de regresión** si se activan flags endurecidos sin pruebas completas |
| Riesgo operativo | **Medio** (piloto controlado) / **Alto** si se publica con defaults de demo |
| **Recomendación final** | **Apto para producción con observaciones** |

“Producción” se interpreta aquí como **despliegue controlado / piloto académico**, no como servicio abierto masivo sin checklist de endurecimiento.

---

## 2. Estado de calidad (FURPS+)

### Veredicto: Cumple parcialmente

**Fundamento (entrada 03 + estado actual)**

- El informe FURPS de implementación concluye **no aprobado el cierre del plan** sobre `main` en `eaac3da`: 0 mejoras nuevas verificadas como avance del plan; 7 parciales solo por capacidades **preexistentes**; 11 no implementadas/no acreditadas.
- Capacidad de producto preexistente (JWT/bcrypt, formularios, arquitectura hexagonal, batería de tests, avisos HU-08) **sí** sostiene un PMV1 usable, pero no equivale a cumplimiento pleno FURPS+.
- Puntaje orientativo del informe 01 (**~62,6/100**) **no fue remedido ni re-medido** tras un plan FURPS ejecutado en remoto.

**Brechas de calidad que siguen condicionando el dictamen**

| Área FURPS+ | Situación |
|---|---|
| Functionality | Flujos core presentes; sin historial GET; curaduría de conocimiento solo vía flag OWASP local |
| Usability | Feedback parcial; catch vacío de contexto y falta de 404 comodín (según 03) sin evidencia de cierre |
| Reliability | Persistencia de consulta no atómica; health/readiness no plenamente diferenciados; backups/RTO no acreditados |
| Performance | Indexación síncrona; sin benchmarks ni cola; dependencia de Ollama |
| Supportability | Sin CI Actions observado; `requirements.txt` con rangos abiertos; RAGAS pendiente de resultados oficiales |

**Nota de sincronización Git:** las remediaciones OWASP existen como cambios **locales sin commit/push**. Quien audite solo `origin/main` no verá aún esa mejora de seguridad. El cierre de calidad institucional requiere versionar y revalidar.

---

## 3. Estado de seguridad (OWASP Top 10)

### Veredicto: Cumple parcialmente

**Fundamento (entrada 06)**

| Indicador | Valor |
|---|---|
| Score inicial (04) | 38 / 100 |
| Score tras remediación (06) | **60 / 100** |
| Categorías corregidas | 1 (A09 logging de aplicación) |
| Parciales | 8 |
| No corregidas | 1 (A06 componentes / supply chain) |

**Cumple parcialmente** porque:

- Hay controles reales en código (JWT enforce en prod, rate limit, roles curator opcionales, CORS estricto, prompt hardening, checksums de modelos, logging de seguridad).
- **No** se alcanza cierre OWASP: defaults de demo dejan varios controles inactivos; A06 sin lock/audit; sesión aún en web storage; rate limit solo en memoria.
- Evidencia dinámica incompleta en el entorno de auditoría (MySQL caído bloqueó 3 tests de login/roles/API con persistencia); 11 tests unitarios de seguridad **sí** pasaron.

**Condición sine qua non para acercarse a “cumple” operativo**

```env
APP_ENV=production
JWT_SECRET=<≥32 caracteres, no default>
KNOWLEDGE_MUTATION_POLICY=curators_only
KNOWLEDGE_CURATOR_EMAILS=...
PASSWORD_POLICY=strong
WEATHER_REQUIRE_AUTH=true
RATE_LIMIT_ENABLED=true
MODEL_INTEGRITY_CHECK=true
URL_ALLOWLIST_ENFORCE=true
```

Sin ese endurecimiento, el dictamen de seguridad **no** habilita exposición pública amplia.

---

## 4. Funcionalidad

### Veredicto: Se preservó la funcionalidad existente

| Criterio | Evaluación |
|---|---|
| Preservación de procesos de negocio | **Sí** — cambios OWASP aditivos (flags, claims `role`, códigos 403/429); rutas de negocio conservadas |
| Regresiones observadas | **No evidenciadas** en comparación funcional de contratos principales; OpenAPI/health se endurecen solo en `production` |
| Riesgos de regresión | **Sí existen** (ver abajo) |

**Riesgos de regresión pendientes de control**

1. Activar `curators_only` sin curadores configurados → bloqueo de ingest/index en demos.
2. `PASSWORD_POLICY=strong` → rechaza registros que antes pasaban con solo 8 caracteres.
3. `WEATHER_REQUIRE_AUTH=true` → rompe clientes que consultaban clima anónimo.
4. Rate limits agresivos / multi-réplica → falsos 429; limiter en memoria no coherente entre instancias.
5. Suite completa de regresión **no** ejecutada aquí con MySQL; CI remoto no acreditado (0 Actions según informe 03).

---

## 5. Riesgo operativo

### Clasificación: Medio (con endurecimiento) — Alto (con defaults de demo)

| Escenario | Riesgo | Motivo |
|---|---|---|
| Piloto académico / aula / usuarios limitados + flags de prod | **Medio** | Controles disponibles; superficie acotada; deuda FURPS conocida |
| Despliegue público con `.env` de desarrollo | **Alto** | Knowledge abierto, password básico, weather público, JWT débil posible, sin backups/CI acreditados |
| Producción masiva con decisiones agronómicas críticas | **Alto** | RAGAS pendiente, HU-08 sintético, sin tenancy pleno ni recuperación acreditada |

---

## 6. Riesgos pendientes (priorizados)

| Prioridad | Riesgo | Origen |
|---|---|---|
| P1 | Remediaciones OWASP no versionadas en `origin/main` | Estado Git local vs remoto |
| P1 | Corpus RAG alterable si knowledge permanece `open` | OWASP A01/A04 |
| P1 | Ausencia acreditada de backups/restauración | FURPS M02 |
| P1 | Suite de regresión + MySQL no verificada en esta auditoría final | Limitación de entorno / FURPS M03 |
| P2 | Persistencia no atómica de consulta/respuesta/evidencias | FURPS M08 |
| P2 | Supply chain Python sin lock/audit (A06 / M14) | OWASP + FURPS |
| P2 | JWT en almacenamiento web (XSS) | OWASP A02/A07 / FURPS M15 |
| P2 | Calidad RAG/HU-08 no validada en campo / RAGAS pendiente | FURPS M09/M10 |
| P3 | Observabilidad (SLO, dashboards) y readiness diferenciado | FURPS M04/M05 |
| P3 | Rate limit no distribuido | OWASP A04/A07 |

---

## 7. Observaciones

1. **Doble pista de auditoría:** FURPS juzgó el cierre del *plan de calidad* sobre `main` remoto; OWASP juzgó *remediaciones de seguridad* sobre el workspace local. El dictamen final integra ambas sin confundir “producto usable” con “planes cerrados”.
2. **Compatibilidad:** la estrategia de flags OWASP fue correcta para no romper demos; el costo es que “código presente ≠ control activo”.
3. **Trazabilidad:** consolidar en Git (`commit` + PR) los cambios de seguridad y los docs `04`–`07` antes de cualquier liberación formal.
4. **Validación mínima pendiente antes de piloto:** MySQL arriba + pytest auth/context/knowledge/roles; smoke login → contexto → consulta; checklist `.env` de producción.
5. **No se autoriza** presentar el sistema como asesoramiento agronómico oficial ni como OWASP “completo”.

---

## 8. Recomendación final

# Apto para producción con observaciones

**Alcance autorizado:** despliegue **controlado** (piloto académico / entorno limitado), siempre que se cumplan las observaciones bloqueantes siguientes.

**Observaciones bloqueantes (obligatorias)**

1. Publicar/versionar remediaciones OWASP y documentación `04`–`07`.
2. Desplegar con `APP_ENV=production` y checklist de secretos/políticas de la sección 3.
3. Ejecutar y archivar suite de regresión con MySQL (auth, contextos, knowledge, roles).
4. Nombrar curadores si se activa escritura restringida de conocimiento.
5. Mantener avisos de prototipo HU-08 / no decisión crítica de campo.

**Observaciones no bloqueantes (deuda explícita)**

- Cerrar ítems FURPS M02, M05, M08, M09 y supply chain (A06).
- Migrar sesión a almacenamiento más seguro (HttpOnly) en una fase posterior.
- Introducir CI con auditoría de dependencias.

**Fuera de alcance de esta aprobación**

- Producción abierta a Internet sin límites de usuarios, sin backups ni monitoreo.
- Uso como sistema oficial de recomendación agrícola.

Si no se cumplen las observaciones bloqueantes, el dictamen se degrada automáticamente a **No apto para producción**.

---

**Firma de dictamen:** Auditor Principal de Calidad y Seguridad — 2026-11-13.  
**Independencia:** síntesis documental basada en entradas FURPS/OWASP y estado observable del workspace; no certifica despliegues productivos no inspeccionados.
