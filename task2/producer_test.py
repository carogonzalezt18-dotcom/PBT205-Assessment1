import pika
import json
import random
import time

print("Producer started")

symbols = ["AAPL", "TSLA", "BTC", "ETH"]
order_types = ["BUY", "SELL"]

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost')
)
channel = connection.channel()

channel.queue_declare(queue='trade_orders')

for i in range(5):  # send 5 messages automatically

    trade_order = {
        "type": random.choice(order_types),
        "symbol": random.choice(symbols),
        "quantity": random.randint(1, 100),
        "price": random.randint(100, 1000),
        "user_id": str(random.randint(100, 999))
    }

    message = json.dumps(trade_order)

    channel.basic_publish(
        exchange='',
        routing_key='trade_orders',
        body=message
    )

    print(f"Sent: {trade_order}")

    time.sleep(1)  # delay to see distribution clearly

connection.close()