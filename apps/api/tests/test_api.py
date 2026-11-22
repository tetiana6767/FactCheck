"""Контрактні тести першого етапу."""

from fastapi.testclient import TestClient

from app.api.routes import get_check_service
from app.main import app
from app.services.check_service import CheckService

client = TestClient(app)


def get_test_check_service() -> CheckService:
    """Не дозволити API-тестам виконувати зовнішні модельні запити."""

    return CheckService()


app.dependency_overrides[get_check_service] = get_test_check_service


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
    assert report["agent_analysis"] is None
    assert report["model_run"]["status"] == "not_configured"
    assert "100%" not in report["explanation"]


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
    assert 'lang="uk"' in response.text
    assert "Перевірити" in response.text
    assert "Налаштування вигляду" in response.text
    assert "рівень довіри" in response.text
    assert "Джерела за і проти" in response.text


def test_web_client_modules_are_served() -> None:
    for path in ("app.js", "report.js", "settings.js", "storage.js"):
        response = client.get(f"/js/{path}")

        assert response.status_code == 200


def test_check_handles_text_without_checkable_claims() -> None:
    response = client.post(
        "/api/check",
        json={"claim": "На мою думку, це чудово. Чи погоджуєтеся ви?"},
    )

    assert response.status_code == 200
    assert response.json()["claims"] == []
    assert response.json()["evidence"] == []


def test_check_keeps_linguistic_signals_separate_from_verdict() -> None:
    response = client.post(
        "/api/check",
        json={"claim": "ТЕРМІНОВО!!! Ви не повірите цій новині."},
    )

    report = response.json()
    assert response.status_code == 200
    assert report["verdict"] == "insufficient_evidence"
    assert {flag["kind"] for flag in report["linguistic_flags"]} == {
        "sensational_phrase",
        "uppercase_emphasis",
        "excessive_punctuation",
    }


def test_check_explains_full_risk_when_no_sources_exist() -> None:
    response = client.post(
        "/api/check",
        json={"claim": "Місяць учора впав на Землю."},
    )

    report = response.json()
    assert response.status_code == 200
    assert report["evidence"] == []
    assert "0% довіри" in report["explanation"]
    assert "100% ризику" in report["explanation"]
