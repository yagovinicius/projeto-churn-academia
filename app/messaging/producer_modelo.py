import pika
import json

def solicitar_atualizacao_modelo():
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()

        # Declara a fila para garantir que exista
        channel.queue_declare(queue='atualiza_modelo', durable=True)

        mensagem = {'acao': 'atualizar_modelo'}

        # Publica mensagem na fila (persistent)
        channel.basic_publish(
            exchange='',
            routing_key='atualiza_modelo',
            body=json.dumps(mensagem),
            properties=pika.BasicProperties(delivery_mode=2)  # Persistente
        )

        print('Solicitação de atualização do modelo enviada com sucesso!')

    except Exception as e:
        print(f'Erro ao enviar solicitação de atualização: {e}')
    finally:
        if 'connection' in locals() and connection.is_open:
            connection.close()

# Teste rápido se executar diretamente
if __name__ == "__main__":
    solicitar_atualizacao_modelo()
