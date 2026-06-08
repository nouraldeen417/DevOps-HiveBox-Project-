from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
from src.app import app, APP_VERSION, get_temperature_status


# ── Helpers ────────────────────────────────────────────────────────────────

def make_mock_response(temp_value, minutes_old=10):
    """
    Builds a fake openSenseMap API response.
    Avoids real HTTP calls — keeps tests fast and reliable.
    """
    created_at = datetime.now(timezone.utc) - timedelta(minutes=minutes_old)
    mock = MagicMock()
    mock.raise_for_status = MagicMock()
    mock.json.return_value = {
        "sensors": [{
            "title": "Temperatur",
            "lastMeasurement": {
                "value": str(temp_value),
                "createdAt": created_at.isoformat().replace("+00:00", "Z")
            }
        }]
    }
    return mock


# ── /version ───────────────────────────────────────────────────────────────

def test_version_returns_200():
    response = app.test_client().get("/version")
    assert response.status_code == 200


def test_version_returns_correct_json():
    response = app.test_client().get("/version")
    assert response.get_json() == {"version": APP_VERSION}


def test_version_value():
    assert APP_VERSION == "0.0.2"


# ── /temperature ───────────────────────────────────────────────────────────

def test_temperature_returns_200_with_valid_data():
    with patch("src.app.requests.get") as mock_get:
        mock_get.return_value = make_mock_response(22.5)
        response = app.test_client().get("/temperature")
        assert response.status_code == 200


def test_temperature_response_shape():
    with patch("src.app.requests.get") as mock_get:
        mock_get.return_value = make_mock_response(22.5)
        data = app.test_client().get("/temperature").get_json()
        assert "average_temperature" in data
        assert "status" in data
        assert data["unit"] == "°C"


def test_temperature_rejects_old_data():
    with patch("src.app.requests.get") as mock_get:
        mock_get.return_value = make_mock_response(22.5, minutes_old=90)
        response = app.test_client().get("/temperature")
        assert response.status_code == 503


def test_temperature_handles_api_failure():
    with patch("src.app.requests.get") as mock_get:
        mock_get.side_effect = Exception("Network error")
        response = app.test_client().get("/temperature")
        assert response.status_code == 503


# ── status logic ───────────────────────────────────────────────────────────

def test_status_too_cold():
    assert get_temperature_status(5) == "Too Cold"


def test_status_good():
    assert get_temperature_status(22) == "Good"


def test_status_too_hot():
    assert get_temperature_status(40) == "Too Hot"


def test_status_boundary_low():
    assert get_temperature_status(10) == "Good"


def test_status_boundary_high():
    assert get_temperature_status(36) == "Good"


# ── /metrics ───────────────────────────────────────────────────────────────

def test_metrics_endpoint_returns_200():
    response = app.test_client().get("/metrics")
    assert response.status_code == 200


def test_metrics_contains_prometheus_data():
    response = app.test_client().get("/metrics")
    assert b"flask_http" in response.data