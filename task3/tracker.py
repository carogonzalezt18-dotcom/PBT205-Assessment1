import sys
import json
from collections import defaultdict

from common import (
    create_connection,
    setup_exchange,
    create_and_bind_queue,
    publish_message
)

# -----------------------------
# CONFIGURATION
# -----------------------------

EXCHANGE_NAME = 'tracking'

# -----------------------------
# DATA STRUCTURES
# -----------------------------

current_positions = {}
contact_events = defaultdict(list)
active_contacts = set()


# -----------------------------
# HELPER FUNCTIONS
# -----------------------------

def register_contact(person_a, person_b, timestamp):
    """
    Register a contact event for both people.
    """
    contact_events[person_a].append({
        "contact": person_b,
        "timestamp": timestamp
    })

    contact_events[person_b].append({
        "contact": person_a,
        "timestamp": timestamp
    })


def get_contact_pair(person_a, person_b):
    """
    Return a sorted tuple so the pair is always stored consistently.
    """
    return tuple(sorted([person_a, person_b]))


def clear_inactive_contacts():
    """
    Remove active contact pairs if the two people are no longer
    in the same position.
    """
    pairs_to_remove = set()

    for pair in active_contacts:
        person_a, person_b = pair

        if person_a not in current_positions or person_b not in current_positions:
            pairs_to_remove.add(pair)
            continue

        if current_positions[person_a] != current_positions[person_b]:
            pairs_to_remove.add(pair)

    active_contacts.difference_update(pairs_to_remove)


def get_reverse_chronological_unique_contacts(person_id):
    """
    Return unique contact names in reverse chronological order.
    """
    if person_id not in contact_events:
        return []

    seen = set()
    unique_contacts = []

    for event in reversed(contact_events[person_id]):
        contact_name = event["contact"]
        if contact_name not in seen:
            seen.add(contact_name)
            unique_contacts.append(contact_name)

    return unique_contacts


def get_reverse_chronological_contact_details(person_id):
    """
    Return unique contacts with their most recent timestamp,
    in reverse chronological order.
    Example:
    [
        {"contact": "Luis", "timestamp": "21:29:39"},
        {"contact": "Ana", "timestamp": "21:10:12"}
    ]
    """
    if person_id not in contact_events:
        return []

    seen = set()
    details = []

    for event in reversed(contact_events[person_id]):
        contact_name = event["contact"]
        if contact_name not in seen:
            seen.add(contact_name)
            details.append({
                "contact": contact_name,
                "timestamp": event["timestamp"]
            })

    return details


def process_position_message(message):
    """
    Update current positions and detect contacts.
    Avoid duplicate contact logging while two people remain together.
    """
    required_fields = ["person_id", "x", "y", "timestamp"]

    for field in required_fields:
        if field not in message:
            print(f"Invalid position message. Missing field: {field}")
            return

    person_id = message["person_id"]
    x = message["x"]
    y = message["y"]
    timestamp = message["timestamp"]

    current_positions[person_id] = (x, y)

    clear_inactive_contacts()

    print(f"[POSITION] {person_id} is now at ({x}, {y}) at {timestamp}")

    for other_person, other_position in current_positions.items():
        if other_person == person_id:
            continue

        if other_position == (x, y):
            pair = get_contact_pair(person_id, other_person)

            if pair not in active_contacts:
                print(f"[CONTACT] {person_id} met {other_person} at ({x}, {y}) at {timestamp}")
                register_contact(person_id, other_person, timestamp)
                active_contacts.add(pair)


def process_query_message(channel, message):
    """
    Process a query and publish a response.
    """
    if "person_id" not in message:
        print("Invalid query message. Missing field: person_id")
        return

    person_id = message["person_id"]
    contacts = get_reverse_chronological_unique_contacts(person_id)
    contact_details = get_reverse_chronological_contact_details(person_id)

    response = {
        "person_id": person_id,
        "contacts": contacts,
        "contact_details": contact_details
    }

    publish_message(
        channel=channel,
        exchange=EXCHANGE_NAME,
        routing_key='query-response',
        message=response
    )

    print(f"[QUERY RESPONSE] Sent contacts for {person_id}: {contacts}")


# -----------------------------
# CALLBACKS
# -----------------------------

def position_callback(ch, method, properties, body):
    try:
        message = json.loads(body.decode())
        process_position_message(message)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except json.JSONDecodeError:
        print("Invalid JSON received on position queue")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print(f"Unexpected error in position callback: {e}")
        ch.basic_ack(delivery_tag=method.delivery_tag)


def query_callback(ch, method, properties, body):
    try:
        message = json.loads(body.decode())
        process_query_message(ch, message)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except json.JSONDecodeError:
        print("Invalid JSON received on query queue")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print(f"Unexpected error in query callback: {e}")
        ch.basic_ack(delivery_tag=method.delivery_tag)


# -----------------------------
# MAIN
# -----------------------------

def main():
    """
    Usage:
    python task3/tracker.py <middleware_endpoint>

    Example:
    python task3/tracker.py localhost
    """
    if len(sys.argv) != 2:
        print("Usage: python task3/tracker.py <middleware_endpoint>")
        sys.exit(1)

    host = sys.argv[1]

    connection, channel = create_connection(host)
    setup_exchange(channel, EXCHANGE_NAME)

    position_queue = create_and_bind_queue(
        channel=channel,
        exchange=EXCHANGE_NAME,
        routing_key='position'
    )

    query_queue = create_and_bind_queue(
        channel=channel,
        exchange=EXCHANGE_NAME,
        routing_key='query'
    )

    print(f"Tracker is running on {host}...")
    print("Waiting for position and query messages...")

    channel.basic_consume(
        queue=position_queue,
        on_message_callback=position_callback,
        auto_ack=False
    )

    channel.basic_consume(
        queue=query_queue,
        on_message_callback=query_callback,
        auto_ack=False
    )

    channel.start_consuming()


if __name__ == "__main__":
    main()