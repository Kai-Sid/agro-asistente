# Reporte de Detección Arquitectónica

## 1. Análisis de Arquitecturas

Basado en la estructura de carpetas y el diseño documentado del proyecto Agro-Asistente, se evalúan los siguientes patrones arquitectónicos:

### 1.1 Arquitectura Hexagonal (Ports and Adapters)
*   **Evidencias:** La carpeta `/backend` está diseñada para aislar el dominio de la infraestructura. Se infiere la presencia de directorios como `domain`, `application`, `infrastructure` y `adapters`.
*   **Nivel de Confianza:** Alto.
*   **Justificación Técnica:** El proyecto requiere que el núcleo de negocio (reglas de consulta agrícola) sea independiente de los agentes externos (Ollama, Chroma, MySQL/TiDB). Esto se evidencia en la capacidad del sistema para alternar entre bases de datos vectoriales (FAISS en la PoC vs. Chroma en producción) sin reescribir el dominio.

### 1.2 Monolito Modular
*   **Evidencias:** Despliegue único mediante `render.yaml`, un solo backend en FastAPI y una sola base de datos relacional.
*   **Nivel de Confianza:** Alto.
*   **Justificación Técnica:** No existen carpetas que sugieran microservicios independientes. Todo el backend se compila y despliega como una sola unidad lógica.

### 1.3 Arquitecturas Descartadas
*   **Microservicios:** Descartada. El tamaño del equipo y la naturaleza académica del proyecto no justifican la complejidad operativa de múltiples servicios.
*   **MVC Tradicional (Backend):** Descartada. Aunque el frontend (React) usa componentes, el backend no sigue el patrón Modelo-Vista-Controlador puro, sino la separación de casos de uso y puertos de la arquitectura hexagonal.

## 2. Conclusión Final
La arquitectura predominante es un **Monolito Modular implementado con Arquitectura Hexagonal**. Esta decisión permite una fácil mantenibilidad del código de IA y prepara el terreno para futuras migraciones (por ejemplo, si se desea pasar el motor de inferencia a un microservicio dedicado).