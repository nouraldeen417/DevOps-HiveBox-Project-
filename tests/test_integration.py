"""Integration tests for HiveBox API — requires running server."""
import requests

BASE_URL = "http://localhost:5000"


def test_version_returns_200():
    """Test version endpoint returns 200."""
    response = requests.get(f"{BASE_URL}/version", timeout=10)
    assert response.status_code == 200


def test_version_has_correct_format():
    """Test version endpoint returns version field."""
    response = requests.get(f"{BASE_URL}/version", timeout=10)
    data = response.json()
    assert "version" in data


def test_temperature_returns_200():
    """Test temperature endpoint returns 200 or 503."""
    response = requests.get(f"{BASE_URL}/temperature", timeout=10)
    assert response.status_code in [200, 503]


def test_temperature_has_status_field():
    """Test temperature endpoint returns valid status field."""
    response = requests.get(f"{BASE_URL}/temperature", timeout=10)
    if response.status_code == 200:
        data = response.json()
        assert "status" in data
        assert data["status"] in ["Too Cold", "Good", "Too Hot"]


def test_metrics_returns_200():
    """Test metrics endpoint returns 200."""
    response = requests.get(f"{BASE_URL}/metrics", timeout=10)
    assert response.status_code == 200


def test_metrics_is_prometheus_format():
    """Test metrics endpoint returns Prometheus format."""
    response = requests.get(f"{BASE_URL}/metrics", timeout=10)
    assert "flask_http_request_total" in response.text
