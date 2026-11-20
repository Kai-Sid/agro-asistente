# Reconstrucción del Entorno e Instalación (CI/CD)

## 1. Infraestructura de Integración Continua (CI)
El proyecto implementa un pipeline de CI/CD utilizando GitHub Actions, configurado en el archivo `.github/workflows/ci.yml`. Esto garantiza que cada Pull Request y Push a la rama `main` o `owasp` pase por un proceso de calidad automatizado.

## 2. Software Requerido y Versiones Recomendadas
El pipeline define dos entornos principales:
*   **Frontend:** Node.js versión 20.
*   **Backend:** Python versión 3.12.

## 3. Procedimiento de Instalación Automatizado
El pipeline ejecuta los siguientes pasos por cada componente:

### A. Job `frontend`
1.  Descarga del código (`actions/checkout@v4`).
2.  Configuración de Node.js 20 con caché de npm.
3.  Instalación estricta de dependencias: `npm ci`.
4.  Ejecución de pruebas: `npm test`.
5.  Construcción del empaquetado de producción: `npm run build`.

### B. Job `backend-unit`
1.  Descarga del código.
2.  Configuración de Python 3.12 con caché de pip.
3.  Instalación de dependencias: `pip install -r requirements.txt`.
4.  Ejecución de pruebas unitarias con Pytest, ignorando pruebas de integración en vivo (MySQL/Ollama) para evitar falsos negativos y estableciendo un entorno de pruebas controlado:
    *   `RATE_LIMIT_ENABLED: "false"`
    *   `APP_ENV: test`
    *   `MYSQL_HOST: "127.0.0.1"`, `MYSQL_PORT: "1"` (puerto inválido intencional).
    *   `JWT_SECRET: "test-secret-key-at-least-32-characters-long"`
    *   `GENERATION_PROVIDER: "template"` (simula el motor de IA).

## 4. Conclusión
El proyecto cuenta con un pipeline de CI que garantiza la compilación del frontend, la correcta instalación de dependencias en el backend y la ejecución de pruebas unitarias, demostrando un alto nivel de madurez en DevOps y asegurando la estabilidad del sistema antes de su despliegue en Render.