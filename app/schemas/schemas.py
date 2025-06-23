from pydantic import BaseModel, EmailStr
from datetime import date, datetime
from enum import Enum


class SexoEnum(str, Enum):
    masculino = "Masculino"
    feminino = "Feminino"


class AlunoCreate(BaseModel):
    nome: str
    sexo: SexoEnum
    email: EmailStr
    senha: str
    data_nascimento: date
    plano_id: int

class AlunoResponse(BaseModel):
    id: int
    nome: str
    sexo: str
    email: EmailStr
    data_nascimento: date
    plano_id: int
    ativo: bool

    class Config:
        from_attributes=True

class CheckinCreate(BaseModel):
    aluno_id: int
    data: date
    hora: datetime

class CheckinResponse(BaseModel):
    id: int
    aluno_id: int
    data: date
    hora: datetime

    class Config:
        from_attributes=True

class PlanoCreate(BaseModel):
    nome: str
    duracao_meses: int
    preco: float

class PlanoResponse(BaseModel):
    id: int
    nome: str
    duracao_meses: int
    preco: float

    class Config:
        from_attributes=True
