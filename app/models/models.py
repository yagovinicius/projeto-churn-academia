import os
from urllib.parse import quote
from datetime import datetime, timezone
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, String, Integer, Float, Boolean, ForeignKey, Date, DateTime
from sqlalchemy.orm import declarative_base, relationship

# carregando aquivo .env
load_dotenv()

usuario = os.getenv('POSTGRES_USER')
senha = quote(os.getenv('POSTGRES_PASSWORD'))
host = os.getenv('POSTGRES_HOST')
porta = os.getenv('POSTGRES_PORT')
banco = os.getenv('POSTGRES_DB')

DATABASE_URL = f'postgresql://{usuario}:{senha}@{host}:{porta}/{banco}'

# criando conexão com o banco
db = create_engine(DATABASE_URL)

# criando base do banco
Base = declarative_base()

# criando as classes/tabelas do banco


class Alunos(Base):
    __tablename__ = 'alunos'

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String, nullable=False)
    sexo = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    senha = Column(String, nullable=False)
    ativo = Column(Boolean, default=True, nullable=False)
    data_nascimento = Column(Date, nullable=False)
    plano_id = Column(Integer, ForeignKey('planos.id'), nullable=False)
    data_cadastro = Column(DateTime(timezone=True), default=lambda: datetime.now(
        timezone.utc), nullable=False)

    plano = relationship('Planos', backref='alunos')


class Checkins(Base):
    __tablename__ = 'checkins'

    id = Column(Integer, primary_key=True, autoincrement=True)
    aluno_id = Column(Integer, ForeignKey('alunos.id'), nullable=False)
    data = Column(Date, default=lambda: datetime.now(
        timezone.utc).date(), nullable=False)
    hora = Column(DateTime(timezone=True), default=lambda: datetime.now(
        timezone.utc), nullable=False)

    aluno = relationship('Alunos', backref='checkins')


class Planos(Base):
    __tablename__ = 'planos'

    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String, nullable=False, unique=True)
    duracao_meses = Column(Integer, nullable=False)
    preco = Column(Float, nullable=False)
