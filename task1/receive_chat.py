import pika

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost')
)

channel = connection.channel()

channel.queue_declare(queue='room')

print("Waiting for messages...")

def callback(ch, method, properties, body):
    print("Received:", body.decode())

channel.basic_consume(
    queue='room',
    on_message_callback=callback,
    auto_ack=True
)

channel.start_consuming()