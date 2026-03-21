import pika
import json
import random
from datetime import datetime

# -----------------------------
# CONNECTION
# -----------------------------

def create_connection(host='localhost'):
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=host)
    )
    channel = connection.channel()
    return connection, channel


# -----------------------------
# EXCHANGE SETUP
# -----------------------------

def setup_exchange(channel, exchange_name='tracking'):
    channel.exchange_declare(
        exchange=exchange_name,
        exchange_type='topic'
    )


# -----------------------------
# PUBLISH MESSAGE
# -----------------------------

def publish_message(channel, exchange, routing_key, message):
    channel.basic_publish(
        exchange=exchange,
        routing_key=routing_key,
        body=json.dumps(message)
    )


# -----------------------------
# CONSUME MESSAGE
# -----------------------------

def start_consuming(channel, queue_name, callback):
    channel.basic_consume(
        queue=queue_name,
        on_message_callback=callback,
        auto_ack=False
    )
    channel.start_consuming()


# -----------------------------
# QUEUE BINDING
# -----------------------------

def create_and_bind_queue(channel, exchange, routing_key):
    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue

    channel.queue_bind(
        exchange=exchange,
        queue=queue_name,
        routing_key=routing_key
    )

    return queue_name


# -----------------------------
# UTILITIES
# -----------------------------

def generate_random_position(board_size):
    return (
        random.randint(0, board_size - 1),
        random.randint(0, board_size - 1)
    )


def get_timestamp():
    return datetime.now().strftime("%H:%M:%S")


def get_random_move():
    moves = [
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1),          (0, 1),
        (1, -1),  (1, 0), (1, 1)
    ]
    return random.choice(moves)


def validate_position(x, y, board_size):
    return 0 <= x < board_size and 0 <= y < board_size