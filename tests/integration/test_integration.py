"""Integration tests for HiveBox API — requires running server."""
import requests
import pytest

BASE_URL = "http://localhost:5000"


# ── /version ───────────────────────────────────────────────────────────────

def test_version_returns_200():
    """Test version endpoint returns 200."""
    response = requests.get(f"{BASE_URL}/version", timeout=5)
    assert response.status_code == 200


def test_version_response_shape():
    """Test version endpoint returns version field."""
    response = requests.get(f"{BASE_URL}/version", timeout=5)
    data = response.json()
    assert "version" in data
    assert isinstance(data["version"], str)


# ── /temperature ───────────────────────────────────────────────────────────

def test_temperature_returns_valid_status_code():
    """Test temperature returns 200 or 503."""
    response = requests.get(f"{BASE_URL}/temperature", timeout=30)
    assert response.status_code in (200, 503)


def test_temperature_response_shape_when_data_available():
    """Test temperature response has correct fields when data available."""
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
    """Test temperature 503 response has correct fields."""
    response = requests.get(f"{BASE_URL}/temperature", timeout=5)
    if response.status_code == 503:
        data = response.json()
        assert "error" in data
        assert "detail" in data


# ── /readyz ────────────────────────────────────────────────────────────────

def test_readyz_returns_valid_status_code():
    """Test readyz returns 200 or 503."""
    response = requests.get(f"{BASE_URL}/readyz", timeout=5)
    assert response.status_code in (200, 503)


def test_readyz_response_shape():
    """Test readyz response has correct fields."""
    response = requests.get(f"{BASE_URL}/readyz", timeout=5)
    data = response.json()
    assert "status" in data
    assert "unreachable_boxes" in data
    assert "cache_fresh" in data


# ── /store ─────────────────────────────────────────────────────────────────
@pytest.mark.skip(reason="Requires MinIO — run after K8s deploy")
def test_store_returns_valid_status_code():
    """Test store returns 200 or 503."""
    response = requests.get(f"{BASE_URL}/store", timeout=5)
    assert response.status_code in (200, 503)


# ── /metrics ───────────────────────────────────────────────────────────────

def test_metrics_returns_200():
    """Test metrics endpoint returns 200."""
    response = requests.get(f"{BASE_URL}/metrics", timeout=5)
    assert response.status_code == 200


def test_metrics_contains_prometheus_data():
    """Test metrics endpoint returns Prometheus format."""
    response = requests.get(f"{BASE_URL}/metrics", timeout=5)
    assert "flask_http" in response.text