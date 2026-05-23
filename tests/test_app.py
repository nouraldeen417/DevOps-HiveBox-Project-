from src.app import app

def test_version():
    client = app.test_client()
    response = client.get("/version")
    assert response.status_code == 200
    assert response.json["version"] == "0.0.1"