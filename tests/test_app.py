"""Unit tests for HiveBox API."""
from datetime import datetime, timezone
from unittest.mock import patch

from src.app import app, get_temperature_status


@patch("src.app.requests.get")
def test_version(mock_get):
    """Test version endpoint returns 200 and correct version."""
    mock_get.return_value.json.return_value = {"version": "0.0.1"}
    client = app.test_client()
    response = client.get("/version")
    assert response.status_code == 200
    assert response.json["version"] == "0.0.1"


@patch("src.app.requests.get")
def test_temperature(mock_get):
    """Test temperature endpoint returns 200 and temperature field."""
    mock_get.return_value.json.return_value = {
        "sensors": [
            {
                "title": "Temperatur",
                "lastMeasurement": {
                    "value": "20.0",
                    "createdAt": datetime.now(timezone.utc).isoformat()
                }
            }
        ]
    }
    client = app.test_client()
    response = client.get("/temperature")
    assert response.status_code == 200
    assert "temperature" in response.json


def test_temperature_status_too_cold():
    """Test status is Too Cold below 10."""
    assert get_temperature_status(5) == "Too Cold"


def test_temperature_status_good():
    """Test status is Good between 11-36."""
    assert get_temperature_status(20) == "Good"


def test_temperature_status_too_hot():
    """Test status is Too Hot above 37."""
    assert get_temperature_status(40) == "Too Hot"
