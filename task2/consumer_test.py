import pika
import json
import time

consumer_name = input("Enter consumer name: ")

# Connect to RabbitMQ
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost')
)
channel = connection.channel()

# Create the queue
channel.queue_declare(queue='trade_orders')

# Fair dispatch: do not send a new message until the previous one is acknowledged
channel.basic_qos(prefetch_count=1)

print(f"{consumer_name} is waiting for messages...")

def callback(ch, method, properties, body):
    try:
        message = json.loads(body.decode())

        required_fields = ["type", "symbol", "quantity", "price", "user_id"]

        for field in required_fields:
            if field not in message:
                print(f"[{consumer_name}] Error: Missing field '{field}'")
                print(f"[{consumer_name}] Invalid message skipped")
                print("-----")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

        print(f"[{consumer_name}] Processing order...")
        time.sleep(2)  # simulate processing time

        print(f"[{consumer_name}] Received order:")
        print(f"[{consumer_name}] Type: {message['type']}")
        print(f"[{consumer_name}] Symbol: {message['symbol']}")
        print(f"[{consumer_name}] Quantity: {message['quantity']}")
        print(f"[{consumer_name}] Price: {message['price']}")
        print(f"[{consumer_name}] User ID: {message['user_id']}")
        print("-----")

        # Acknowledge only after successful processing
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except json.JSONDecodeError:
        print(f"[{consumer_name}] Error: Invalid JSON format")
        print(f"[{consumer_name}] Invalid message skipped")
        print("-----")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print(f"[{consumer_name}] Unexpected error: {e}")
        print(f"[{consumer_name}] Message skipped")
        print("-----")
        ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_consume(
    queue='trade_orders',
    on_message_callback=callback,
    auto_ack=False
)

channel.start_consuming()