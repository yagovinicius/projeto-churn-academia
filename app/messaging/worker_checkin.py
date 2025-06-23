# worker_checkin.py
import pika
import json
from sqlalchemy.orm import sessionmaker
from app.models import db, Checkins
from datetime import date, datetime

def salvar_checkin(dados):
    if 'data' in dados:
        dados['data'] = date.fromisoformat(dados['data'])
    if 'hora' in dados:
        dados['hora'] = datetime.fromisoformat(dados['hora'])

    Session = sessionmaker(bind=db)
    session = Session()
    try:
        novo = Checkins(**dados)
        session.add(novo)
        session.commit()
        print(f"check-in feito: {dados}")
    except Exception as e:
        session.rollback()
        print(f"erro no check-in: {e}")
    finally:
        session.close()
def iniciar_worker():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='checkin_fila', durable=True)

    def callback(ch, method, properties, body):
        dados = json.loads(body)
        salvar_checkin(dados)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='checkin_fila', on_message_callback=callback)
    print('Worker escutando fila checkin_fila...')
    channel.start_consuming()

if __name__ == "__main__":
    iniciar_worker()
