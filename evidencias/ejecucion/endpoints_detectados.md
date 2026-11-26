# Endpoints Detectados (API REST)
*   `GET /health` -> Verifica estado del sistema y BD.
*   `POST /api/v1/auth/register` -> Registro de agricultores.
*   `POST /api/v1/auth/login` -> Autenticación (JWT).
*   `GET /api/v1/contexts` -> Listar contextos agrícolas.
*   `POST /api/v1/contexts` -> Crear contexto agrícola.
*   `POST /api/v1/queries` -> Consulta principal (RAG + SLM).
*   `POST /api/v1/queries/riesgo` -> Predicción experimental (Random Forest).