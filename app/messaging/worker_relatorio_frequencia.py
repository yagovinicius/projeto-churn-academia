import pika
import json
import os
import pandas as pd
from sqlalchemy.orm import sessionmaker
from app.models import db, Checkins, Alunos
from datetime import datetime

def gerar_relatorio_frequencia(data_referencia_str):
    data_referencia = datetime.fromisoformat(data_referencia_str).date()

    Session = sessionmaker(bind=db)
    session = Session()

    try:
        # JOIN entre Checkins e Alunos para evitar múltiplas queries
        resultados = (
            session.query(Checkins, Alunos)
            .join(Alunos, Checkins.aluno_id == Alunos.id)
            .filter(Checkins.data == data_referencia)
            .all()
        )

        if not resultados:
            print(f'Nenhum check-in encontrado para {data_referencia}')
            return

        # Montar DataFrame
        dados = []
        for checkin, aluno in resultados:
            dados.append({
                'aluno_id': checkin.aluno_id,
                'nome_aluno': aluno.nome,
                'data': checkin.data.isoformat(),
                'hora': checkin.hora.isoformat() if checkin.hora else None
            })

        df = pd.DataFrame(dados)

        # Garante que o diretório 'relatorios/' existe
        os.makedirs('relatorios', exist_ok=True)

        # Salvar arquivo CSV
        nome_arquivo = f'relatorios/relatorio_frequencia_{data_referencia}.csv'
        df.to_csv(nome_arquivo, index=False)
        print(f'Relatório salvo: {nome_arquivo}')

    except Exception as e:
        print(f'Erro ao gerar relatório: {e}')
    finally:
        session.close()

def callback(ch, method, properties, body):
    mensagem = json.loads(body)
    data_ref = mensagem.get('data')
    if not data_ref:
        print('Mensagem inválida: falta campo data')
        ch.basic_ack(delivery_tag=method.delivery_tag)
        return
    gerar_relatorio_frequencia(data_ref)
    ch.basic_ack(delivery_tag=method.delivery_tag)

def iniciar_worker():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='relatorio_frequencia', durable=True)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='relatorio_frequencia', on_message_callback=callback)
    print('Worker escutando fila relatorio_frequencia...')
    channel.start_consuming()

if __name__ == "__main__":
    iniciar_worker()
