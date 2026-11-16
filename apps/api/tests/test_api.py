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
    report = response.json()
    assert report["claim"] == "Київ — столиця України."
    assert report["verdict"] == "insufficient_evidence"
    assert report["claims"] == [
        {
            "id": "claim-1",
            "text": "Київ — столиця України.",
            "start": 0,
            "end": 23,
        }
    ]
    assert report["evidence"][0]["claim_id"] == "claim-1"
    assert report["evidence_snapshot"]["items"] == report["evidence"]


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


def test_check_handles_text_without_checkable_claims() -> None:
    response = client.post(
        "/api/check",
        json={"claim": "На мою думку, це чудово. Чи погоджуєтеся ви?"},
    )

    assert response.status_code == 200
    assert response.json()["claims"] == []
    assert response.json()["evidence"] == []
