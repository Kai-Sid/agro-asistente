# Auditoría de Dependencias - Backend (FastAPI)

## 1. Inventario de Dependencias de Producción
El backend utiliza un archivo `requirements.txt` declarativo. Las dependencias críticas se clasifican en:

| Categoría | Dependencia | Versión | Propósito |
| :--- | :--- | :--- | :--- |
| **Core Web** | `fastapi` | >=0.115.0,<1 | Framework web moderno para construir la API REST. |
| **Core Web** | `uvicorn` | >=0.32.0,<1 | Servidor ASGI de alto rendimiento para FastAPI. |
| **Datos** | `pydantic` | >=2.9.0,<3 | Validación de datos y modelado de esquemas. |
| **Persistencia** | `sqlalchemy` | >=2.0.36,<3 | ORM para la gestión de la base de datos relacional. |
| **Persistencia** | `pymysql` | >=1.1.1,<2 | Driver para conectarse a MySQL/TiDB Cloud. |
| **Vector DB** | `chromadb` | >=0.5.23,<2 | Base de datos vectorial para el motor RAG. |
| **Seguridad** | `bcrypt` | >=4.2.0,<6 | Hashing seguro de contraseñas de usuarios. |
| **Seguridad** | `pyjwt` | >=2.10.0,<3 | Generación y validación de tokens JWT. |
| **Red** | `httpx` | >=0.27.2,<1 | Cliente HTTP para consumir Ollama y SENAMHI. |
| **IA / ML** | `ragas` | ==0.4.3 | Framework para evaluar la calidad del RAG. |
| **IA / ML** | `scikit-learn` | >=1.6.0,<2 | Modelos de Machine Learning (TF-IDF, Random Forest). |
| **IA / ML** | `joblib` | >=1.4.0,<2 | Serialización del modelo de ML experimental. |

## 2. Dependencias de Desarrollo
| `pytest` | >=8.3.0,<10 | Framework para la ejecución de pruebas unitarias y de integración. |

## 3. Análisis de Seguridad
*   **Buenas Prácticas:** Se utiliza `requirements.lock.txt` para una instalación reproducible de auditoría, mitigando el riesgo de ataques de supply chain (OWASP A06).
*   **Nota de Arquitectura:** La dependencia de Ollama no se hace mediante SDK oficial, sino mediante peticiones HTTP con `httpx` a la API `/api/generate`, manteniendo el desacoplamiento del núcleo (Arquitectura Hexagonal).