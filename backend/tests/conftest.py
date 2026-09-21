import os

# Los tests unitarios y HTTP no requieren Ollama. El proveedor activo de PMV1
# sigue siendo ollama en .env.example; pytest fuerza plantilla salvo integración.
if os.environ.get("OLLAMA_INTEGRATION") != "1":
    os.environ["GENERATION_PROVIDER"] = "template"
