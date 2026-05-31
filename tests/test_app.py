from src.app import app
from unittest.mock import patch
from datetime import datetime, timezone


@patch("src.app.requests.get")
def test_version(mock_get):
    mock_get.return_value.json.return_value = {"version": "0.0.1"}
    client = app.test_client()
    response = client.get("/version")
    assert response.status_code == 200
    assert response.json["version"] == "0.0.1"


@patch("src.app.requests.get")
def test_temperature(mock_get):
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
