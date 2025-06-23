import pika
import json
from datetime import date

def solicitar_relatorio_frequencia(data_referencia: date):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='relatorio_frequencia', durable=True)

    mensagem = {'data': data_referencia.isoformat()}

    channel.basic_publish(
        exchange='',
        routing_key='relatorio_frequencia',
        body=json.dumps(mensagem),
        properties=pika.BasicProperties(delivery_mode=2)
    )
    connection.close()