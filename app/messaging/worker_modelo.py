import pika
import json
import os
import pandas as pd
from sqlalchemy.orm import sessionmaker
from app.models import db, Alunos, Checkins
from datetime import datetime
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

def carregar_dados():
    # conexão ao banco
    Session = sessionmaker(bind=db)
    session = Session()
    
    try:
        # Lê dados de alunos e checkins direto do banco
        alunos = session.query(Alunos).all()
        checkins = session.query(Checkins).all()

        # Converte para DataFrames (você pode adaptar isso conforme o que tiver)
        df_alunos = pd.DataFrame([a.__dict__ for a in alunos])
        df_checkins = pd.DataFrame([c.__dict__ for c in checkins])
        
        # Remove colunas do SQLAlchemy que não interessam (_sa_instance_state)
        if '_sa_instance_state' in df_alunos.columns:
            df_alunos.drop(columns=['_sa_instance_state'], inplace=True)
        if '_sa_instance_state' in df_checkins.columns:
            df_checkins.drop(columns=['_sa_instance_state'], inplace=True)

        return df_alunos, df_checkins
    finally:
        session.close()

def preparar_base(df_alunos, df_checkins):

    # Conversão datas
    df_alunos['data_nascimento'] = pd.to_datetime(df_alunos['data_nascimento'])
    hoje = pd.to_datetime(datetime.now().date())
    df_alunos['Idade'] = df_alunos['data_nascimento'].apply(
        lambda nascimento: hoje.year - nascimento.year - ((hoje.month, hoje.day) < (nascimento.month, nascimento.day))
    )

    # Último checkin por aluno
    df_checkins['data'] = pd.to_datetime(df_checkins['data'])
    ultimo_checkin = df_checkins.groupby('aluno_id')['data'].max().reset_index()
    ultimo_checkin.rename(columns={'data': 'data_ultimo_checkin'}, inplace=True)
    ultimo_checkin['DiasSemCheckin'] = (hoje - ultimo_checkin['data_ultimo_checkin']).dt.days

    # Unir
    base = pd.merge(df_alunos, ultimo_checkin, left_on='id', right_on='aluno_id', how='left')
    base.drop(columns=['aluno_id'], inplace=True)

    # Checkins totais e últimos 30, 90 dias
    total_checkins = df_checkins.groupby('aluno_id').size().reset_index(name='TotalCheckins')
    checkins_30 = df_checkins[df_checkins['data'] >= (hoje - pd.Timedelta(days=30))]
    checkins_30d = checkins_30.groupby('aluno_id').size().reset_index(name='CheckinsUltimos30Dias')
    checkins_90 = df_checkins[df_checkins['data'] >= (hoje - pd.Timedelta(days=90))]
    checkins_90d = checkins_90.groupby('aluno_id').size().reset_index(name='CheckinsUltimos90Dias')
    checkins_90d['MediaSemanalCheckin_90d'] = checkins_90d['CheckinsUltimos90Dias'] / (90 / 7)

    base = base.merge(total_checkins, left_on='id', right_on='aluno_id', how='left')
    base = base.merge(checkins_30d, left_on='id', right_on='aluno_id', how='left')
    base = base.merge(checkins_90d[['aluno_id', 'CheckinsUltimos90Dias', 'MediaSemanalCheckin_90d']], left_on='id', right_on='aluno_id', how='left')

    # Preencher NaNs
    base.fillna(0, inplace=True)

    # Criar target churn
    base['É_Churn'] = base['DiasSemCheckin'] >= 30
    base['É_Churn'] = base['É_Churn'].astype(int)

    # Drop colunas irrelevantes
    drop_cols = ['id', 'ativo', 'data_nascimento', 'data_cadastro', 'data_ultimo_checkin',
                 'nome', 'email', 'senha', 'sexo']  # ajuste conforme seu df
    for c in drop_cols:
        if c in base.columns:
            base.drop(columns=[c], inplace=True)

    # Separa X e y
    X = base.drop(columns=['É_Churn', 'DiasSemCheckin', 'CheckinsUltimos30Dias'], errors='ignore')
    y = base['É_Churn']

    return X, y

def treinar_modelo(X, y):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    return model

def salvar_modelo(model):
    caminho = os.path.join(os.path.dirname(__file__), '..', 'modelo_churn_atualizado.pkl')
    joblib.dump(model, caminho)
    print(f'Modelo salvo em {caminho}')

def callback(ch, method, properties, body):
    print("Recebida solicitação para atualizar modelo")
    try:
        df_alunos, df_checkins = carregar_dados()
        X, y = preparar_base(df_alunos, df_checkins)
        modelo = treinar_modelo(X, y)
        salvar_modelo(modelo)
        print("Modelo atualizado com sucesso")
    except Exception as e:
        print(f"Erro ao atualizar modelo: {e}")
    ch.basic_ack(delivery_tag=method.delivery_tag)

def iniciar_worker():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='atualiza_modelo', durable=True)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='atualiza_modelo', on_message_callback=callback)
    print('Worker escutando fila atualiza_modelo...')
    channel.start_consuming()

if __name__ == "__main__":
    iniciar_worker()
