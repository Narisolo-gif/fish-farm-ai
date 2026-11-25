from fastapi.testclient import TestClient

from app.main import app


def test_health():
    # Le service répond même sans LLM configuré : la plateforme reste utilisable.
    reponse = TestClient(app).get("/health")

    assert reponse.status_code == 200
    assert reponse.json() == {"status": "ok"}
