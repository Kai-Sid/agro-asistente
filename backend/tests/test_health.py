from fastapi.testclient import TestClient

from app.main import app
from app.infrastructure.adapters.output.mysql.connection import ping_mysql
from app.infrastructure.config.settings import get_settings

client = TestClient(app)


def test_health_returns_ok() -> None:
    response = client.get("/health")
    payload = response.json()

    assert response.status_code == 200
    assert payload["status"] == "ok"
    assert payload["service"] == "agro-asistente"
    assert payload["phase"] == "1"
    assert payload["architecture"] == "hexagonal"
    assert payload["mysql"] in {"connected", "disconnected"}


def test_health_ready_refleja_estado_mysql() -> None:
    response = client.get("/health/ready")
    mysql_ok = ping_mysql(get_settings())
    if mysql_ok:
        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "ready"
        assert payload["mysql"] == "connected"
    else:
        assert response.status_code == 503
