from app.routers.aluno_routes import aluno_router
from fastapi import FastAPI, Depends, HTTPException
from dotenv import load_dotenv
import os
from app.security import pwd_context
import joblib
from app.tasks.scheduler import agendar_envio_relatorio
from fastapi.security import OAuth2PasswordRequestForm
from app.auth import create_access_token, require_admin, require_aluno
from app.modelo import modelo_churn

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')

app = FastAPI(title="API Academia Churn",
              description="API para monitoramento de frequência e previsão de churn de alunos.", version="1.0.0")

# importando modelo
# modelo_churn = joblib.load('ml/modelo_churn.pkl')

# importando roteadores

app.include_router(aluno_router)


@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Usuários de exemplo
    if form_data.username == "admin" and form_data.password == "admin":
        access_token = create_access_token({"sub": "admin", "role": "admin"})
        return {"access_token": access_token, "token_type": "bearer"}
    elif form_data.username == "aluno" and form_data.password == "aluno":
        access_token = create_access_token({"sub": "aluno", "role": "aluno"})
        return {"access_token": access_token, "token_type": "bearer"}
    else:
        raise HTTPException(
            status_code=400, detail="Usuário ou senha inválidos")

# Exemplo de proteção de endpoint (aplique conforme necessário)
# @app.get("/admin-only")
# def admin_only(user=Depends(require_admin)):
#     return {"msg": "Acesso de admin liberado!"}
