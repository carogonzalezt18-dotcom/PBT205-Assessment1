import sys
import time

from common import (
    create_connection,
    setup_exchange,
    publish_message,
    generate_random_position,
    get_timestamp,
    get_random_move,
    validate_position
)

# -----------------------------
# CONFIG
# -----------------------------

EXCHANGE_NAME = 'tracking'


def main():
    """
    Usage:
    python task3/person.py <middleware_endpoint> <person_id> <speed_seconds> <board_size>

    Example:
    python task3/person.py localhost Ana 1 10
    """
    if len(sys.argv) != 5:
        print("Usage: python task3/person.py <middleware_endpoint> <person_id> <speed_seconds> <board_size>")
        sys.exit(1)

    host = sys.argv[1]
    person_id = sys.argv[2]

    try:
        speed = float(sys.argv[3])
    except ValueError:
        print("Error: speed_seconds must be a number.")
        sys.exit(1)

    try:
        board_size = int(sys.argv[4])
    except ValueError:
        print("Error: board_size must be an integer.")
        sys.exit(1)

    if speed <= 0:
        print("Error: speed_seconds must be greater than 0.")
        sys.exit(1)

    if board_size < 1 or board_size > 1000:
        print("Error: board_size must be between 1 and 1000.")
        sys.exit(1)

    connection, channel = create_connection(host)
    setup_exchange(channel, EXCHANGE_NAME)

    # Initial random position
    x, y = generate_random_position(board_size)

    print(f"{person_id} connected to {host}")
    print(f"{person_id} starting at position ({x}, {y}) on a {board_size}x{board_size} board")
    print(f"{person_id} will move every {speed} second(s)")

    while True:
        timestamp = get_timestamp()

        message = {
            "person_id": person_id,
            "x": x,
            "y": y,
            "timestamp": timestamp
        }

        publish_message(
            channel=channel,
            exchange=EXCHANGE_NAME,
            routing_key='position',
            message=message
        )

        print(f"[{person_id}] Sent position: ({x}, {y}) at {timestamp}")

        # Generate one random move like a king in chess
        dx, dy = get_random_move()
        new_x = x + dx
        new_y = y + dy

        # Prevent moving off the board
        if validate_position(new_x, new_y, board_size):
            x, y = new_x, new_y

        time.sleep(speed)


if __name__ == "__main__":
    main()