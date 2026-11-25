# Protocolo de usabilidad PMV3

Estado: **prueba simulada con perfiles sintéticos completada (2026-11-25)**.  
**No** se ejecutaron sesiones con agricultores ni usuarios reales. La prueba con personas reales queda **fuera del alcance de este cierre** y deberá realizarse en una fase posterior.

Tipo de evidencia: **prueba simulada con perfiles sintéticos** (`SIM-01`, `SIM-02`, `SIM-03`).  
No hay declaraciones, entrevistas ni observaciones humanas inventadas.

## Objetivo

Comprobar, mediante recorridos instrumentados en el navegador del entorno local, que los flujos principales de agricultor se pueden completar, que los errores son recuperables y que la UI responde en escritorio y en ~360 px de ancho.

## Preparación

- Versión/rama: `codex/pmv3-stored-procedures-readiness` (cambios locales sin commit)
- Fecha: 2026-11-25
- Entorno: Laragon · API `127.0.0.1:8010` · Vite `127.0.0.1:5173` · Ollama activo (`qwen2.5:1.5b`)
- Herramienta: navegador integrado Cursor (inspección + interacción; no hay suite Playwright/Cypress del repo)
- Facilitador: agente de validación técnica
- Perfiles: `SIM-01`, `SIM-02`, `SIM-03` (cuentas sintéticas `*.pmv3.usabilidad@test.local`)
- Consentimiento: no aplica (no hay personas reales)

## Tareas del protocolo

1. Crear cuenta de agricultor.
2. Iniciar sesión.
3. Crear y seleccionar contexto agrícola.
4. Enviar consulta con Ollama y revisar respuesta/evidencias.
5. Recuperarse de credenciales incorrectas y campos vacíos.
6. Repetir flujo principal en viewport ~360 px.
7. Comprobar ausencia de HTTP 500 / errores JS en los flujos.

## Registro por perfil sintético

| Código | Dispositivo | Tareas completadas / total | Tiempo medido | Pidió ayuda | Errores / bloqueos observados | Respuesta/evidencias visibles | Comentarios técnicos |
|---|---|---:|---|---|---|---|---|
| SIM-01 | Escritorio 1280×800 | 5/5 (registro→login→contexto→selección→consulta) | Consulta: **107005.5 ms** (`performance.measure`) | N/A (simulado) | Tras “Seleccionar”, navegar a Consulta demasiado pronto mostró “sin contexto”; se corrigió refetch en `QueryPage` | Sí | Flujo principal aprobado tras corrección |
| SIM-02 | Escritorio | Recuperación de error + login correcto | No cronometrado (sin marca de rendimiento en ese tramo) | N/A | Credenciales inválidas → mensaje **«Credenciales inválidas»**; campos vacíos → validación HTML | N/A en este perfil | Tras corrección, vacío muestra **«Completa este campo.»** en español |
| SIM-03 | Móvil 360×740 | 4/4 (login→contexto→selección→consulta) | Consulta: **127196.3 ms** | N/A | Ninguno bloqueante; `scrollWidth=360`, sin scroll horizontal | Sí | Menú colapsable; contenido esencial visible |

## Resultados por flujo

| Flujo | Resultado | Mensaje/bloqueo | Completable sin guía del sistema | Observación comprobable |
|---|---|---|---|---|
| Registro agricultor (SIM-01) | **Aprobado** | «Registro exitoso…» + redirect a login | Sí | Formulario completo, labels visibles |
| Login correcto | **Aprobado** | Panel con nombre del perfil sintético | Sí | — |
| Contexto crear/seleccionar | **Aprobado** | «Contexto agrícola creado.» / «Contexto seleccionado.» / «En uso» | Sí | Esperar «En uso» antes de consultar |
| Consulta + evidencias (Ollama) | **Aprobado** | Respuesta + lista Evidencias | Sí | Latencia alta (~107–127 s medidas) |
| Credenciales incorrectas | **Aprobado** | «Credenciales inválidas» | Sí | Permite corregir y reintentar |
| Campos obligatorios vacíos | **Aprobado** (tras fix) | Antes: inglés del navegador; después: «Completa este campo.» | Sí | `lang=es` + `validacionEsp.js` |
| Móvil ~360 px | **Aprobado** | Menú colapsado; sin scroll horizontal de página | Sí | Capturas en `docs/evidencia_pmv3/hu17/` |

## Hallazgos y correcciones

| Hallazgo observado | Impacto | Cambio realizado | Revisión posterior |
|---|---|---|---|
| Consulta podía mostrar “sin contexto” si se navegaba antes de terminar la selección | Medio | `frontend/src/pages/QueryPage.jsx`: refetch al montar/ruta y al recuperar foco | Reprobado en SIM-01 inicial; aprobado al reentrar a `/query` y en SIM-03 |
| Validación HTML5 en inglés pese a `lang="es"` | Bajo–medio | `frontend/src/forms/validacionEsp.js` + Login/Register/Context | Comprobado: mensaje «Completa este campo.» |
| Latencia de consulta Ollama > 100 s | Observación | Sin cambio de código (timeout de consulta ya 120 s) | Documentar expectativa de espera |

## Evidencia visual

Carpeta: `docs/evidencia_pmv3/hu17/`

- `hu17_sim01_consulta_escritorio.png`
- `hu17_sim02_credenciales_invalidas.png`
- `hu17_sim03_dashboard_360.png`
- `hu17_sim03_consulta_360.png`

## Resumen

- Perfiles sintéticos que completaron registro/login/consulta sin bloqueo final: **3 / 3** (SIM-02 enfocado en recuperación; registro vía API sintético + login UI)
- Tareas con mayor fricción: selección de contexto vs. navegación inmediata a Consulta; latencia Ollama
- Problemas en móvil: **no** se observó corte esencial ni scroll horizontal (`scrollWidth === clientWidth === 360`)
- Errores HTTP 500 / JS: **no** observados en consola instrumentada durante los flujos
- Recomendación de cierre HU-17 en este ciclo: **cerrar con evidencia simulada**, dejando explícito que **falta prueba con usuarios reales**

## Limitación explícita

Esta hoja **no** afirma validación con personas reales. HU-17 queda cerrada solo como **usabilidad técnica simulada** para el PMV3 local; la validación de campo con agricultores/usuarios representativos permanece pendiente.
