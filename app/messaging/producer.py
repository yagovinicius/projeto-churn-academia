import pika
import json
from datetime import date, datetime

def converter_dados(dados):
    return {
        chave: valor.isoformat() if isinstance(valor, (date, datetime)) else valor
        for chave, valor in dados.items()
    }

def enviar_para_fila_checkin(dados_checkin: dict):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='checkin_fila', durable=True)

    # converte datas antes de serializar
    dados_convertidos = converter_dados(dados_checkin)
    body = json.dumps(dados_convertidos)

    channel.basic_publish(
        exchange='',
        routing_key='checkin_fila',
        body=body,
        properties=pika.BasicProperties(delivery_mode=2)
    )

    connection.close()
