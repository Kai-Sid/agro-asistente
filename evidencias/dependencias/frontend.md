# Auditoría de Dependencias - Frontend (React)

## 1. Inventario de Dependencias de Producción
Basado en el análisis del archivo `package-lock.json`, el frontend utiliza las siguientes librerías principales:

| Dependencia | Versión Detectada | Propósito / Justificación Técnica |
| :--- | :--- | :--- |
| `react` | ^18.3.1 | Biblioteca principal para la construcción de interfaces de usuario (UI). |
| `react-dom` | ^18.3.1 | Renderizado de componentes React en el DOM del navegador. |
| `react-router` | ^7.9.4 | Enrutamiento del lado del cliente para la navegación SPA. |
| `react-router-dom` | ^7.9.4 | Integración del enrutador con el DOM (enlaces, historial). |
| `axios` | ^1.21.1 | Cliente HTTP basado en promesas para consumir la API REST del backend. |

## 2. Dependencias de Desarrollo (DevDependencies)
| Dependencia | Versión Detectada | Propósito |
| :--- | :--- | :--- |
| `vite` | 5.4.21 | Empaquetador y servidor de desarrollo ultrarrápido. |
| `@vitejs/plugin-react` | 4.3.4 | Plugin de Vite para soportar Fast Refresh y JSX de React. |

## 3. Análisis de Seguridad y Calidad
*   **Mantenibilidad:** Las versiones están fijadas con el prefijo `^` (caret), lo que permite actualizaciones menores y parches, manteniendo la estabilidad.
*   **Riesgos:** Se recomienda ejecutar auditorías periódicas con `npm audit` para mitigar vulnerabilidades en las dependencias transitivas.