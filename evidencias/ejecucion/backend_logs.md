# Análisis de logs del backend (Fase 4, Prompt 6)

## Alcance y método

- **Archivos analizados:** `backend_logs_intento1_bloqueo.txt`, `backend_logs.txt` y `pip_install_log.txt` (carpeta `evidencias/ejecucion/`).
- **Método:** búsqueda de patrones (errores, advertencias, excepciones, conexiones, códigos HTTP) con un máximo de 40 coincidencias por archivo. Los números de línea corresponden a los archivos originales.
- **Regla:** solo se registra lo que consta en los logs o en la salida de consola. Lo demás figura como «No evidenciado».
- **Entorno:** Windows, Python 3.13.17, entorno virtual `backend/venv`, backend sin servidor MySQL local.
- **Limitación:** el resumen cubre solo las primeras 40 coincidencias de `backend_logs.txt`. Por eso el segundo y el tercer intento de login y el registro (todos con 500) no tienen número de línea en esta matriz.

## Matriz de hallazgos

| ID | Categoría | Hallazgo | Evidencia (archivo:línea) | Severidad |
|---|---|---|---|---|
| B-01 | Configuración | Windows bloqueó la extensión compilada `_processors_cy` de SQLAlchemy (directiva de Control de aplicaciones) y el backend no arrancó en el primer intento. Afecta solo a equipos con esa directiva. | `backend_logs_intento1_bloqueo.txt:1`, `:83` | Alto |
| B-02 | Configuración | Desviación del entorno estándar: para arrancar se renombraron a mano los 8 archivos `.pyd` de SQLAlchemy y la librería corre en modo Python puro. | Acción manual del auditor, no consta en los logs. Arranque posterior exitoso: `backend_logs.txt:2-4` | Medio |
| B-03 | Configuración | No hay servidor MySQL disponible: la conexión apunta a `localhost` y falla con `OperationalError 2003`. | `backend_logs.txt:75`, `:251` | Alto |
| B-04 | Red | Conexión TCP rechazada al intentar abrir la base de datos (`ConnectionRefusedError`, WinError 10061). Es la misma causa que B-03. | `backend_logs.txt:25` | Alto |
| B-05 | Excepción | `POST /api/v1/auth/login` responde 500 y la excepción no se controla (`Exception in ASGI application`). Ocurrió en 3 de 3 intentos. | `backend_logs.txt:13`, `:14`, `:253`; el tercer intento consta solo en la salida de consola | Alto |
| B-06 | Excepción | `POST /api/v1/auth/register` responde 500 por la misma causa. | Línea no evidenciada en este resumen; consta en la salida de consola de la prueba | Alto |
| B-07 | Configuración | `/health` maneja la desconexión (responde 200 con `mysql: disconnected`), pero login y registro no la manejan. | `backend_logs.txt:5`, `:11`, `:12`; el cuerpo de la respuesta consta solo en la salida de consola | Medio |
| B-08 | Autenticación | `GET /api/v1/weather/observations` responde 200 sin sesión. Si es intencional: No evidenciado. | `backend_logs.txt:10` | Medio |
| B-09 | Autenticación | `/api/v1/contexts` y `/api/v1/knowledge/documents` responden 401 sin sesión. Comportamiento esperado, se registra como informativo. | `backend_logs.txt:8`, `:9` | Bajo |
| B-10 | Configuración | Las líneas de log de uvicorn no incluyen fecha ni hora, lo que impide reconstruir cuándo ocurrió cada evento. | `backend_logs.txt:2-13` | Bajo |
| B-11 | Dependencias | El resolvedor de pip avisó dos veces de que tardaba más de lo normal y sugirió restricciones de versión más estrictas. | `pip_install_log.txt:258`, `:358` | Bajo |
| B-12 | Dependencias | `pytest` se instala junto con las dependencias de producción. | `pip_install_log.txt:556` (visible en la salida completa; recortada en el resumen) | Bajo |

## Cobertura por categoría solicitada

| Categoría | Resultado |
|---|---|
| Errores | B-01, B-03, B-05, B-06 |
| Advertencias | B-11 |
| Excepciones | B-05, B-06 |
| Dependencias faltantes | Ninguna evidenciada: la instalación terminó con `Successfully installed` (`pip_install_log.txt:556`) |
| Problemas de configuración | B-01, B-02, B-03, B-07, B-10 |
| Problemas de red | B-04 |
| Problemas de autenticación | B-08, B-09 |

Total: 12 hallazgos (0 críticos, 5 altos, 3 medios, 4 bajos).
