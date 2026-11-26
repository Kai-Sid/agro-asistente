# Reconstrucción del Dominio
- **Entidades:** Agricultor, ContextoAgrícola, Consulta, Respuesta.
- **Reglas de Negocio:** Un agricultor debe tener un contexto seleccionado antes de consultar. El sistema no debe generar respuestas si el motor RAG no recupera evidencia suficiente (umbral de similitud).