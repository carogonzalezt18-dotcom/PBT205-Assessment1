import pika

# Connection settings
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost')
)

channel = connection.channel()

print("Connected successfully to RabbitMQ!")

connection.close()
