"""Unit tests for HiveBox API."""
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from src.app import app
from src.config import APP_VERSION
from src.temperature import get_temperature_status


# ── Helpers ────────────────────────────────────────────────────────────────

def make_mock_response(temp_value, minutes_old=10):
    """Build a fake openSenseMap API response."""
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
    """Test version endpoint returns 200."""
    response = app.test_client().get("/version")
    assert response.status_code == 200


def test_version_returns_correct_json():
    """Test version endpoint returns correct version."""
    response = app.test_client().get("/version")
    assert response.get_json() == {"version": APP_VERSION}


def test_version_value():
    """Test APP_VERSION is correct."""
    assert APP_VERSION == "0.0.2"


# ── /temperature ───────────────────────────────────────────────────────────

def test_temperature_returns_200_with_valid_data():
    """Test temperature returns 200 with valid fresh data."""
    with patch("src.temperature.requests.get") as mock_get:
        mock_get.return_value = make_mock_response(22.5)
        response = app.test_client().get("/temperature")
        assert response.status_code == 200


def test_temperature_response_shape():
    """Test temperature response has correct fields."""
    with patch("src.temperature.requests.get") as mock_get:
        mock_get.return_value = make_mock_response(22.5)
        data = app.test_client().get("/temperature").get_json()
        assert "average_temperature" in data
        assert "status" in data
        assert data["unit"] == "°C"


def test_temperature_rejects_old_data():
    """Test temperature returns 503 when data is older than 1 hour."""
    with patch("src.temperature.requests.get") as mock_get:
        mock_get.return_value = make_mock_response(22.5, minutes_old=90)
        response = app.test_client().get("/temperature")
        assert response.status_code == 503


def test_temperature_handles_api_failure():
    """Test temperature returns 503 when API call fails."""
    with patch("src.temperature.requests.get") as mock_get:
        mock_get.side_effect = Exception("Network error")
        response = app.test_client().get("/temperature")
        assert response.status_code == 503


# ── status logic ───────────────────────────────────────────────────────────

def test_status_too_cold():
    """Test Too Cold status below 10."""
    assert get_temperature_status(5) == "Too Cold"


def test_status_good():
    """Test Good status between 10 and 36."""
    assert get_temperature_status(22) == "Good"


def test_status_too_hot():
    """Test Too Hot status above 36."""
    assert get_temperature_status(40) == "Too Hot"


def test_status_boundary_low():
    """Test boundary at exactly 10."""
    assert get_temperature_status(10) == "Good"


def test_status_boundary_high():
    """Test boundary at exactly 36."""
    assert get_temperature_status(36) == "Good"


# ── /metrics ───────────────────────────────────────────────────────────────

def test_metrics_endpoint_returns_200():
    """Test metrics endpoint returns 200."""
    response = app.test_client().get("/metrics")
    assert response.status_code == 200


def test_metrics_contains_prometheus_data():
    """Test metrics endpoint returns Prometheus format."""
    response = app.test_client().get("/metrics")
    assert b"flask_http" in response.data