import sys
import json

from common import (
    create_connection,
    setup_exchange,
    create_and_bind_queue,
    publish_message
)

# -----------------------------
# CONFIG
# -----------------------------

EXCHANGE_NAME = 'tracking'


def main():
    """
    Usage:
    python task3/query.py <middleware_endpoint> <person_id>

    Example:
    python task3/query.py localhost Ana
    """
    if len(sys.argv) != 3:
        print("Usage: python task3/query.py <middleware_endpoint> <person_id>")
        sys.exit(1)

    host = sys.argv[1]
    person_id = sys.argv[2]

    connection, channel = create_connection(host)
    setup_exchange(channel, EXCHANGE_NAME)

    # Create a temporary queue to receive query responses
    response_queue = create_and_bind_queue(
        channel=channel,
        exchange=EXCHANGE_NAME,
        routing_key='query-response'
    )

    # Send the query
    query_message = {
        "person_id": person_id
    }

    publish_message(
        channel=channel,
        exchange=EXCHANGE_NAME,
        routing_key='query',
        message=query_message
    )

    print(f"Query sent for {person_id} to {host}. Waiting for response...")

    def callback(ch, method, properties, body):
        try:
            message = json.loads(body.decode())

            if message.get("person_id") == person_id:
                contacts = message.get("contacts", [])

                print(f"\nContacts for {person_id}:")
                if contacts:
                    for contact in contacts:
                        print(f"- {contact}")
                else:
                    print("No contacts found.")

                ch.basic_ack(delivery_tag=method.delivery_tag)
                ch.stop_consuming()
            else:
                ch.basic_ack(delivery_tag=method.delivery_tag)

        except json.JSONDecodeError:
            print("Invalid JSON received in query response.")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            ch.stop_consuming()

        except Exception as e:
            print(f"Unexpected error in query response: {e}")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            ch.stop_consuming()

    channel.basic_consume(
        queue=response_queue,
        on_message_callback=callback,
        auto_ack=False
    )

    channel.start_consuming()
    connection.close()


if __name__ == "__main__":
    main()