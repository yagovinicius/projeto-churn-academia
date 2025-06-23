# Projeto Academia Churn

Sistema para monitoramento de frequência de alunos e previsão de churn em academias.

## Funcionalidades
- Cadastro de alunos
- Registro de check-in
- Consulta de frequência
- Previsão de risco de churn
- Processamento assíncrono com RabbitMQ
- Geração de relatórios automáticos
- Atualização automática do modelo de IA
- Autenticação JWT (admin e aluno)

## Tecnologias
- Python 3.10+
- FastAPI
- SQLAlchemy
- PostgreSQL
- RabbitMQ
- Pydantic
- Scikit-learn
- Docker
- Faker (popular banco)

## Instalação e Execução (Docker)

1. **Clone o repositório:**
   ```bash
   git clone <seu-fork>
   cd projeto-academia-churn
   ```
2. **Suba tudo com Docker Compose:**
   ```bash
   docker-compose up --build
   ```
   Isso irá subir:
   - API FastAPI (porta 8000)
   - PostgreSQL (porta 5432)
   - RabbitMQ (porta 5672 e 15672)

3. **Acesse a documentação da API:**
   - [http://localhost:8000/docs](http://localhost:8000/docs)

4. **(Opcional) Inicialize as tabelas:**
   ```bash
   docker-compose exec app python scripts/init_db.py
   ```

5. **Popule o banco com dados fake:**
   - Com a API rodando, execute:
   ```bash
   python faker-academia.py
   ```
   Isso irá criar planos, alunos e checkins automaticamente via API.

6. **Execute os workers RabbitMQ:**
   Em terminais separados, rode:
   ```bash
   docker-compose exec app python app/messaging/worker_checkin.py
   docker-compose exec app python app/messaging/worker_relatorio_frequencia.py
   docker-compose exec app python app/messaging/worker_modelo.py
   ```

7. **Testes automatizados:**
   ```bash
   pytest
   ```
   Ou:
   ```bash
   python tests/test_full_flow.py
   ```

## Autenticação JWT
- **Endpoint de login:** `POST /token`
- **Usuários de exemplo:**
  - admin / admin
  - aluno / aluno
- **No Swagger:** Clique em "Authorize", preencha apenas username e password, e clique em Authorize.

## Requisitos Atendidos

- API REST completa e documentada
- Banco de dados PostgreSQL integrado
- Processamento assíncrono com RabbitMQ
- Modelo de IA para previsão de churn
- Script para popular o banco com dados realistas
- Testes automatizados
- Documentação via Swagger
- Autenticação JWT (admin e aluno)
- Pronto para Docker

## Observações

O projeto está pronto para ser clonado e executado conforme as instruções acima.
Para dúvidas ou sugestões, consulte a documentação da API.
