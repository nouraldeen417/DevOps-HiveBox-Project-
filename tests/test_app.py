# conftest.py already handled the path
# so we import directly from app
from app import app, APP_VERSION


def test_version_endpoint_returns_200():
    """
    /version must exist and return HTTP 200.
    Fails if: route is missing or Flask isn't set up correctly.
    """
    client = app.test_client()
    response = client.get("/version")
    assert response.status_code == 200


def test_version_endpoint_returns_correct_json():
    """
    /version must return the correct JSON body.
    Fails if: route works but returns wrong data.
    """
    client = app.test_client()
    response = client.get("/version")
    assert response.get_json() == {"version": APP_VERSION}


def test_version_value():
    """
    APP_VERSION must be exactly 0.0.1.
    Fails if: someone changed the version incorrectly.
    """
    assert APP_VERSION == "0.0.1"