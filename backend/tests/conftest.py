import os

# Los tests unitarios y HTTP no requieren Ollama. El proveedor activo de PMV1
# sigue siendo ollama en .env.example; pytest fuerza plantilla salvo integración.
_valor_integracion = (
    os.environ.get("RUN_OLLAMA_INTEGRATION_TESTS")
    or os.environ.get("OLLAMA_INTEGRATION")
    or ""
).strip().lower()
if _valor_integracion not in {"1", "true", "yes"}:
    os.environ["GENERATION_PROVIDER"] = "template"

# Evita 429 flaky en la suite; la remediación se cubre en tests dedicados.
os.environ["RATE_LIMIT_ENABLED"] = "false"
os.environ["APP_ENV"] = "development"
os.environ["JWT_SECRET_ENFORCE"] = "false"
os.environ["URL_ALLOWLIST_ENFORCE"] = "false"
os.environ["JWT_SECRET"] = "test-secret-key-at-least-32-characters-long"
os.environ["KNOWLEDGE_MUTATION_POLICY"] = "open"
os.environ["WEATHER_REQUIRE_AUTH"] = "false"
os.environ["PASSWORD_POLICY"] = "basic"
