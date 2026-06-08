import requests

BASE_URL = "http://localhost:5000"


# ── /version ───────────────────────────────────────────────────────────────

def test_version_returns_200():
    response = requests.get(f"{BASE_URL}/version", timeout=5)
    assert response.status_code == 200


def test_version_response_shape():
    response = requests.get(f"{BASE_URL}/version", timeout=5)
    data = response.json()
    assert "version" in data
    assert isinstance(data["version"], str)


# ── /temperature ───────────────────────────────────────────────────────────

def test_temperature_returns_valid_status_code():
    response = requests.get(f"{BASE_URL}/temperature", timeout=5)
    # 200 = live data available, 503 = all boxes stale — both are correct
    assert response.status_code in (200, 503)


def test_temperature_response_shape_when_data_available():
    response = requests.get(f"{BASE_URL}/temperature", timeout=5)
    if response.status_code == 200:
        data = response.json()
        assert "average_temperature" in data
        assert "unit" in data
        assert "status" in data
        assert "boxes_used" in data
        assert "boxes_total" in data
        assert data["unit"] == "°C"
        assert data["status"] in ("Too Cold", "Good", "Too Hot")


def test_temperature_503_shape_when_no_data():
    response = requests.get(f"{BASE_URL}/temperature", timeout=5)
    if response.status_code == 503:
        data = response.json()
        assert "error" in data
        assert "detail" in data


# ── /metrics ───────────────────────────────────────────────────────────────

def test_metrics_returns_200():
    response = requests.get(f"{BASE_URL}/metrics", timeout=5)
    assert response.status_code == 200


def test_metrics_contains_prometheus_data():
    response = requests.get(f"{BASE_URL}/metrics", timeout=5)
    assert "flask_http" in response.text