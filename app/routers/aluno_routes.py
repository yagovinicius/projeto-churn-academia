import numpy as np
import pandas as pd
from app.security import pwd_context
from app.modelo import modelo_churn
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker
from app.models.models import Alunos, Checkins, Planos, db
from app.schemas.schemas import AlunoCreate, AlunoResponse, CheckinCreate, CheckinResponse, PlanoCreate, PlanoResponse
from app.messaging.producer import enviar_para_fila_checkin
from app.auth import require_admin, require_aluno

# criando roteador
aluno_router = APIRouter(prefix='/aluno', tags=['alunos'])

# criando rotas


@aluno_router.get('/')
async def home():
    '''
    Rota padrão do sistema. Todas as rotas precisam de autenticação.
    '''
    return {'status': 'API em funcionamento',
            'usuario_autenticado': False}

# rotas get


@aluno_router.get('/{id}', response_model=AlunoResponse)
async def obter_registro(aluno_id: int, user=Depends(require_admin)):
    '''
    Consulta os dados de um aluno pelo id
    '''
    Session = sessionmaker(bind=db)
    session = Session()
    try:
        aluno = session.query(Alunos).filter(Alunos.id == aluno_id).first()
        if not aluno:
            raise HTTPException(status_code=404, detail='Aluno não encontrado')
        return aluno
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        session.close()


@aluno_router.get('/{id}/frequencia')
async def obter_frequencia(aluno_id: int, user=Depends(require_aluno)):
    ''''
    Consultar todos os checkins feitos por aluno
    '''
    Session = sessionmaker()
    session = Session()
    try:
        aluno = session.query(Alunos).filter(Alunos.id == aluno_id).first()
        if not aluno:
            raise HTTPException(status_code=404, detail='Aluno não encontrado')
        frequencia = session.query(Checkins).filter(
            Checkins.aluno_id == aluno_id).all()
        return {'frequencia': [f.data for f in frequencia]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        session.close()


@aluno_router.get('/{id}/risco-churn')
async def obter_risco_churn(aluno_id: int, user=Depends(require_admin)):
    '''
    Retorna o risco de Churn de um aluno
    '''
    Session = sessionmaker(bind=db)
    session = Session()
    try:
        aluno = session.query(Alunos).filter(Alunos.id == aluno_id).first()
        if not aluno:
            raise HTTPException(status_code=404, detail='Aluno não encontrado')

        checkins = session.query(Checkins).filter(
            Checkins.aluno_id == aluno_id).order_by(Checkins.data).all()
        if not checkins:
            raise HTTPException(
                status_code=404, detail='Nenhum check-in encontrado')

        hoje = pd.to_datetime(datetime.now().date())
        datas = pd.to_datetime([c.data for c in checkins])
        datas_ordenadas = np.sort(datas)

        total_checkins = len(datas_ordenadas)
        ultimos_90d = datas_ordenadas[datas_ordenadas >= (
            hoje - pd.Timedelta(days=90))]
        checkins_90d = len(ultimos_90d)
        media_semanal_90d = checkins_90d / (90 / 7)

        if total_checkins > 1:
            intervalos = np.diff(datas_ordenadas).astype(
                'timedelta64[D]').astype(int)
            media_intervalo = intervalos.mean()
            desvio_intervalo = intervalos.std()
        else:
            media_intervalo = 0
            desvio_intervalo = 0

        nascimento = aluno.data_nascimento
        idade = hoje.year - nascimento.year - \
            ((hoje.month, hoje.day) < (nascimento.month, nascimento.day))
        is_male = 1 if str(aluno.sexo) == "Masculino" else 0

        df_pred = pd.DataFrame([{
            'plano_id': aluno.plano_id,
            'IsMale': is_male,
            'Idade': idade,
            'TotalCheckins': total_checkins,
            'CheckinsUltimos90Dias': checkins_90d,  # <-- incluído aqui
            'MediaSemanalCheckin_90d': media_semanal_90d,
            'TempoMedioEntreCheckins': media_intervalo,
            'DesvioDiasEntreCheckins': desvio_intervalo
        }])

        risco = modelo_churn.predict_proba(df_pred)[0][1]
        porcentagem = round(risco * 100)
        return {'id': aluno_id, 'risco_churn': f'{porcentagem}%'}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        session.close()

# rotas post


@aluno_router.post('/registro', response_model=AlunoResponse)
async def criar_novo_registro(aluno: AlunoCreate, user=Depends(require_admin)):
    '''
    Cria uma sessão para a verificação, validação e integração de um novo aluno
    '''
    Session = sessionmaker(bind=db)
    session = Session()
    try:

        senha_hash = pwd_context.hash(aluno.senha)

        novo_aluno = Alunos(
            nome=aluno.nome,
            sexo=aluno.sexo,
            email=aluno.email,
            senha=senha_hash,
            data_nascimento=aluno.data_nascimento,
            plano_id=aluno.plano_id
        )
        session.add(novo_aluno)
        session.commit()
        session.refresh(novo_aluno)  # pegar o id
        return novo_aluno
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(
            status_code=400, detail='E-mail já cadastrado.') from exc
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        session.close()


@aluno_router.post('/checkin')
async def criar_checkin_em_fila(check_in: CheckinCreate, user=Depends(require_aluno)):
    '''
    Envia o check-in para fila RabbitMQ para ser processado de forma assíncrona
    '''
    try:
        enviar_para_fila_checkin(check_in.dict())
        return {'mensagem': 'Check-in enviado para processamento assíncrono'}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f'Erro ao enviar para a fila: {str(e)}')


@aluno_router.post('/planos', response_model=PlanoResponse)
async def criar_novo_plano(plano: PlanoCreate, user=Depends(require_admin)):
    '''
    Cria uma sessão para a verificação, validação e integração de um novo plano
    '''
    Session = sessionmaker(bind=db)
    session = Session()
    try:
        novo_plano = Planos(
            nome=plano.nome,
            duracao_meses=plano.duracao_meses,
            preco=plano.preco
        )
        session.add(novo_plano)
        session.commit()
        session.refresh(novo_plano)
        return novo_plano
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(
            status_code=400, detail='Plano já cadastrado') from exc
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        session.close()

# rotas update


@aluno_router.put('/registro/{aluno_id}', response_model=AlunoResponse)
async def atualizar_aluno(aluno_id: int, aluno: AlunoCreate):
    '''
    Atualizar cadastro de aluno por id
    '''
    Session = sessionmaker(bind=db)
    session = Session()
    try:
        aluno_db = session.query(Alunos).filter(Alunos.id == aluno_id).first()
        if not aluno_db:
            raise HTTPException(status_code=404, detail='Aluno não encontrado')
        # Atualiza os campos
        aluno_db.nome = aluno.nome
        aluno_db.sexo = aluno.sexo
        aluno_db.email = aluno.email
        aluno_db.senha = pwd_context.hash(aluno.senha)
        aluno_db.data_nascimento = aluno.data_nascimento
        aluno_db.plano_id = aluno.plano_id
        session.commit()
        session.refresh(aluno_db)
        return aluno_db
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(
            status_code=400, detail='E-mail já cadastrado.') from exc
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        session.close()


@aluno_router.put('/planos/{plano_id}', response_model=PlanoResponse)
async def atualizar_plano(plano_id: int, plano: PlanoCreate):
    '''
    Atualizar plano por id
    '''
    Session = sessionmaker(bind=db)
    session = Session()
    try:
        plano_db = session.query(Planos).filter(Planos.id == plano_id).first()
        if not plano_db:
            raise HTTPException(status_code=404, detail='Plano não encontrado')
        plano_db.nome = plano.nome
        plano_db.duracao_meses = plano.duracao_meses
        plano_db.preco = plano.preco
        session.commit()
        session.refresh(plano_db)
        return plano_db
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(
            status_code=400, detail='Plano já cadastrado.') from exc
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        session.close()

# rotas delete


@aluno_router.delete('/registro/{aluno_id}')
async def deletar_aluno(aluno_id: int):
    '''
    Deletar registro por id
    '''
    Session = sessionmaker(bind=db)
    session = Session()
    try:
        aluno_db = session.query(Alunos).filter(Alunos.id == aluno_id).first()
        if not aluno_db:
            raise HTTPException(status_code=404, detail='Aluno não encontrado')
        session.delete(aluno_db)
        session.commit()
        return {'mensagem': 'Aluno removido com sucesso'}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        session.close()


@aluno_router.delete('/planos/{plano_id}')
async def deletar_plano(plano_id: int):
    '''
    Deletar plano por id
    '''
    Session = sessionmaker(bind=db)
    session = Session()
    try:
        plano_db = session.query(Planos).filter(Planos.id == plano_id).first()
        if not plano_db:
            raise HTTPException(status_code=404, detail='Plano não encontrado')
        session.delete(plano_db)
        session.commit()
        return {'mensagem': 'Plano removido com sucesso'}
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        session.close()
