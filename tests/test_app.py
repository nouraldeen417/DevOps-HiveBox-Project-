from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from src.app import app, APP_VERSION

# ─── /version tests (unchanged from Phase 2) ───────────────────────────────

def test_version_endpoint_returns_200():
    client = app.test_client()
    response = client.get("/version")
    assert response.status_code == 200


def test_version_endpoint_returns_correct_json():
    client = app.test_client()
    response = client.get("/version")
    assert response.get_json() == {"version": APP_VERSION}


def test_version_value():
    assert APP_VERSION == "0.0.1"


# ─── /temperature tests (new in Phase 3) ───────────────────────────────────

def make_mock_response(temp_value, minutes_old=10):
    """
    Helper that builds a fake openSenseMap API response.
    We use this so tests don't make real HTTP calls — fast and reliable.
    """
    created_at = datetime.now(timezone.utc)
    from datetime import timedelta
    created_at = created_at - timedelta(minutes=minutes_old)

    mock = MagicMock()
    mock.json.return_value = {
        "sensors": [
            {
                "title": "Temperatur",
                "lastMeasurement": {
                    "value": str(temp_value),
                    "createdAt": created_at.isoformat().replace("+00:00", "Z")
                }
            }
        ]
    }
    mock.raise_for_status = MagicMock()
    return mock


def test_temperature_endpoint_returns_200():
    """
    /temperature must return 200 when valid data is available.
    We mock the HTTP calls so no real internet needed.
    """
    with patch("app.requests.get") as mock_get:
        mock_get.return_value = make_mock_response(22.5)
        client = app.test_client()
        response = client.get("/temperature")
        assert response.status_code == 200


def test_temperature_returns_average():
    """
    /temperature must return the correct average across all boxes.
    """
    with patch("app.requests.get") as mock_get:
        mock_get.return_value = make_mock_response(22.5)
        client = app.test_client()
        response = client.get("/temperature")
        data = response.get_json()
        assert "average_temperature" in data
        assert data["unit"] == "°C"


def test_temperature_rejects_old_data():
    """
    /temperature must return 503 if all data is older than 1 hour.
    """
    with patch("app.requests.get") as mock_get:
        # 90 minutes old — should be rejected
        mock_get.return_value = make_mock_response(22.5, minutes_old=90)
        client = app.test_client()
        response = client.get("/temperature")
        assert response.status_code == 503


def test_temperature_handles_api_failure():
    """
    /temperature must return 503 if all boxes are unreachable.
    """
    with patch("app.requests.get") as mock_get:
        mock_get.side_effect = Exception("Network error")
        client = app.test_client()
        response = client.get("/temperature")
        assert response.status_code == 503