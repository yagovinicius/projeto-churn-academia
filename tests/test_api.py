import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_docs():
    response = client.get("/docs")
    assert response.status_code == 200


def test_home():
    response = client.get("/aluno/")
    assert response.status_code == 200
    assert "status" in response.json()
