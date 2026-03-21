import pika
import threading
import sys
import time

if len(sys.argv) != 4:
    print("Usage: python chat.py <username> <port> <room>")
    sys.exit(1)

username = sys.argv[1]
port = int(sys.argv[2])
room_name = sys.argv[3]

stop_event = threading.Event()

# Sending connection
send_connection = pika.BlockingConnection(
    pika.ConnectionParameters(host="localhost", port=port)
)
send_channel = send_connection.channel()
send_channel.exchange_declare(exchange=room_name, exchange_type="fanout")

# Receiving connection
receive_connection = pika.BlockingConnection(
    pika.ConnectionParameters(host="localhost", port=port)
)
receive_channel = receive_connection.channel()
receive_channel.exchange_declare(exchange=room_name, exchange_type="fanout")

# Create a unique queue for this user
result = receive_channel.queue_declare(queue="", exclusive=True)
queue_name = result.method.queue
receive_channel.queue_bind(exchange=room_name, queue=queue_name)

print(f"Connected to chat as {username} in room '{room_name}'. Type messages and press Enter.")
print("Type !exit to leave the chat.")

def receive_messages():
    while not stop_event.is_set():
        try:
            method_frame, header_frame, body = receive_channel.basic_get(
                queue=queue_name,
                auto_ack=True
            )

            if body:
                message = body.decode()
                if not message.startswith(username + ":"):
                    print(f"\n{message}")

            time.sleep(0.1)

        except Exception:
            break

receiver_thread = threading.Thread(target=receive_messages)
receiver_thread.start()

try:
    while True:
        message_text = input()

        if message_text == "!exit":
            print("Exiting chat...")
            stop_event.set()
            break

        full_message = f"{username}: {message_text}"

        send_channel.basic_publish(
            exchange=room_name,
            routing_key="",
            body=full_message
        )

except KeyboardInterrupt:
    print("\nExiting chat...")
    stop_event.set()

finally:
    receiver_thread.join(timeout=2)

    try:
        if receive_channel.is_open:
            receive_channel.close()
    except Exception:
        pass

    try:
        if receive_connection.is_open:
            receive_connection.close()
    except Exception:
        pass

    try:
        if send_channel.is_open:
            send_channel.close()
    except Exception:
        pass

    try:
        if send_connection.is_open:
            send_connection.close()
    except Exception:
        pass
    