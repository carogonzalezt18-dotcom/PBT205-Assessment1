import pika
import json
import sys

# Check command-line arguments
if len(sys.argv) != 2:
    print("Usage: python tradeListener.py <endpoint>")
    sys.exit(1)

endpoint = sys.argv[1]

# Connect to RabbitMQ
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host=endpoint)
)
channel = connection.channel()

# Declare trades exchange
channel.exchange_declare(exchange='trades', exchange_type='fanout')

# Create temporary queue and bind it to the trades exchange
result = channel.queue_declare(queue='', exclusive=True)
queue_name = result.method.queue
channel.queue_bind(exchange='trades', queue=queue_name)

print("Trade listener is waiting for trades...")

def callback(ch, method, properties, body):
    try:
        trade = json.loads(body.decode())

        print("Trade received:")
        print(f"Buyer: {trade['buyer']}")
        print(f"Seller: {trade['seller']}")
        print(f"Stock: {trade['stock']}")
        print(f"Quantity: {trade['quantity']}")
        print(f"Trade Price: {trade['trade_price']}")
        print("-----")

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print(f"Error reading trade: {e}")
        ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_qos(prefetch_count=1)

channel.basic_consume(
    queue=queue_name,
    on_message_callback=callback,
    auto_ack=False
)

channel.start_consuming()