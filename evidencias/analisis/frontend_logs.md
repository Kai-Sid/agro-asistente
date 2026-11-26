# Análisis de logs del frontend (Fase 4, Prompt 6)

## Alcance y método

- **Archivos analizados:** `frontend_logs.txt`, `npm_install_log.txt` y `npm_audit.txt` (carpeta `evidencias/ejecucion/`).
- **Método:** búsqueda de patrones (errores, advertencias, vulnerabilidades, severidades) con un máximo de 40 coincidencias por archivo. Los números de línea corresponden a los archivos originales.
- **Regla:** solo se registra lo que consta en los logs, en la salida de consola o en la captura de pantalla. Lo demás figura como «No evidenciado».
- **Entorno:** Windows, Node v26.13.1, Vite 5.4.11, servidor de desarrollo en `127.0.0.1:5173`.

## Matriz de hallazgos

| ID | Categoría | Hallazgo | Evidencia (archivo:línea) | Severidad |
|---|---|---|---|---|
| F-01 | Dependencias | `npm audit` reporta 6 vulnerabilidades: 3 moderadas y 3 altas. | `npm_install_log.txt:7`, `npm_audit.txt:39` | Alto |
| F-02 | Dependencias | `esbuild` en versiones hasta 0.24.2 aparece con severidad moderada. | `npm_audit.txt:4` (el paquete y el rango constan en la salida de consola) | Medio |
| F-03 | Dependencias | React Router tiene al menos dos avisos: redirección abierta con barra invertida en `<Link>` y `useNavigate` (GHSA-wrjc-x8rr-h8h6) e inyección de constructor en la hidratación SSR (GHSA-337j-9hxr-rhxg). La severidad exacta de cada aviso consta en `npm_audit.txt`. | `npm_audit.txt:24`; el primer aviso consta en la salida de consola | Alto |
| F-04 | Configuración | `npm` avisa de que el paquete `esbuild@0.21.5` tiene un script `postinstall` no cubierto por `allowScripts`. | `npm_install_log.txt:16-19` | Bajo |
| F-05 | Configuración | `frontend_logs.txt` contiene códigos ANSI de color, lo que dificulta analizar el log como texto plano. | `frontend_logs.txt:6` | Bajo |
| F-06 | Autenticación | Ante un 500 o un error de red, el login muestra el mensaje genérico «No se pudo iniciar sesión. Inténtalo de nuevo.». El 401 sí se distingue en el código y muestra «Credenciales inválidas». El mensaje genérico no orienta al usuario sobre un fallo del servicio. | `LoginPage.jsx` (manejo de errores); captura `03_login_error.png` (pendiente de guardar en `capturas/`); el 500 consta en `backend_logs.md` B-05 | Bajo |

## Observaciones sin hallazgo

- `frontend_logs.txt:6`: Vite 5.4.11 arrancó en 974 ms sin errores ni advertencias, y `http://127.0.0.1:5173` respondió 200.
- Instalación (`npm ci`): terminó sin errores. Las únicas advertencias son F-01 y F-04.
- Dependencias faltantes: ninguna evidenciada.
- Problemas de red del frontend: ninguno evidenciado en sus logs.

## Pendientes de verificación

- Hay dos bloques de `npm_audit.txt` marcados con severidad alta (líneas 14 y 33) cuyo paquete no se identifica en este resumen. Revisar el archivo completo.
- La captura `03_login_error.png` debe guardarse en `evidencias/ejecucion/capturas/` con un correo ficticio.

Total: 6 hallazgos (0 críticos, 2 altos, 1 medio, 3 bajos).
