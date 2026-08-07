import pytest
from fastapi.testclient import TestClient
from documentor.web.main import app

client = TestClient(app)

def test_api_docs_invalid_path():
    response = client.get("/api/docs?path=/path/that/does/not/exist")
    assert response.status_code == 400
    assert "Provided path is not a valid directory." in response.json()["detail"]

def test_api_generate_invalid_path():
    response = client.post("/api/generate", json={
        "path": "/path/that/does/not/exist",
        "model": "gemini/gemini-3.6-flash"
    })
    assert response.status_code == 400
    assert "Provided path is not a valid directory." in response.json()["detail"]

def test_api_chat_no_vector_db(tmp_path):
    response = client.post("/api/chat", json={
        "path": str(tmp_path),
        "query": "Hello",
        "model": "gemini/gemini-3.6-flash"
    })
    assert response.status_code == 400
    assert "Vector store not found. Generate documentation first." in response.json()["detail"]

def test_static_files():
    # Attempt to load the root which should serve index.html
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
