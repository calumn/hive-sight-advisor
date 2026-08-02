from fastapi.testclient import TestClient

from hive_sight_advisor_api.main import app


def test_health_returns_ok() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"service": "advisor-api", "status": "ok"}
