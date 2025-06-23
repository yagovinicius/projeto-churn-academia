import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.security import pwd_context

client = TestClient(app)

ADMIN = {"username": "admin", "password": "admin"}
ALUNO = {"username": "aluno", "password": "aluno"}

# Dados de exemplo para registro de aluno
novo_aluno = {
    "nome": "Teste User",
    "sexo": "Masculino",
    "email": "testeuser@example.com",
    "senha": "123456",
    "data_nascimento": "2000-01-01",
    "plano_id": 1
}


def get_token(user):
    resp = client.post("/token", data=user)
    assert resp.status_code == 200
    return resp.json()["access_token"]


def test_full_flow():
    # 1. Login como admin
    admin_token = get_token(ADMIN)
    headers_admin = {"Authorization": f"Bearer {admin_token}"}

    # 2. Registrar novo aluno
    resp = client.post("/aluno/registro", json=novo_aluno,
                       headers=headers_admin)
    assert resp.status_code == 200
    aluno_id = resp.json()["id"]

    # 3. Login como aluno
    aluno_token = get_token(ALUNO)
    headers_aluno = {"Authorization": f"Bearer {aluno_token}"}

    # 4. Fazer checkin
    checkin = {
        "aluno_id": aluno_id,
        "data": "2024-01-01",
        "hora": "2024-01-01T08:00:00"
    }
    resp = client.post("/aluno/checkin", json=checkin, headers=headers_aluno)
    assert resp.status_code == 200
    assert "mensagem" in resp.json()

    # 5. Consultar frequência
    resp = client.get(f"/aluno/{aluno_id}/frequencia", headers=headers_aluno)
    assert resp.status_code == 200
    assert "frequencia" in resp.json()

    # 6. Consultar risco de churn (admin)
    resp = client.get(f"/aluno/{aluno_id}/risco-churn", headers=headers_admin)
    assert resp.status_code == 200
    assert "risco_churn" in resp.json()
