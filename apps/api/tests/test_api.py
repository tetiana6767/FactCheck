"""Контрактні тести першого етапу."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ready_status() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_check_returns_deterministic_report() -> None:
    response = client.post("/api/check", json={"claim": "  Київ — столиця України.  "})

    assert response.status_code == 200
    assert response.json() == {
        "claim": "Київ — столиця України.",
        "verdict": "insufficient_evidence",
        "explanation": (
            "Твердження прийнято до аналізу. Пошук і перевірку джерел "
            "буде підключено на наступному етапі, тому доказів для "
            "фактологічного висновку поки недостатньо."
        ),
        "linguistic_flags": [],
        "evidence": [],
    }


def test_check_rejects_empty_claim() -> None:
    response = client.post("/api/check", json={"claim": "   "})

    assert response.status_code == 422


def test_check_rejects_too_long_claim() -> None:
    response = client.post("/api/check", json={"claim": "а" * 10_001})

    assert response.status_code == 422


def test_web_client_is_served() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "FactCheck" in response.text
