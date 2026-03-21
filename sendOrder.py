import pika
import json
import sys


def print_usage():
    print("Base usage: python sendOrder.py <username> <endpoint> <side> <quantity> <price>")
    print("Extended usage: python sendOrder.py <username> <endpoint> <stock> <side> <quantity> <price>")


# Support both:
# 1) Base version: username endpoint side quantity price
# 2) Extended version: username endpoint stock side quantity price
if len(sys.argv) == 6:
    username = sys.argv[1]
    endpoint = sys.argv[2]
    stock = "XYZ"
    side = sys.argv[3].upper()

    try:
        quantity = int(sys.argv[4])
    except ValueError:
        print("Error: quantity must be an integer")
        sys.exit(1)

    try:
        price = float(sys.argv[5])
    except ValueError:
        print("Error: price must be a number")
        sys.exit(1)

elif len(sys.argv) == 7:
    username = sys.argv[1]
    endpoint = sys.argv[2]
    stock = sys.argv[3].upper()
    side = sys.argv[4].upper()

    try:
        quantity = int(sys.argv[5])
    except ValueError:
        print("Error: quantity must be an integer")
        sys.exit(1)

    try:
        price = float(sys.argv[6])
    except ValueError:
        print("Error: price must be a number")
        sys.exit(1)

else:
    print_usage()
    sys.exit(1)

# Validate side
if side not in ["BUY", "SELL"]:
    print("Error: side must be BUY or SELL")
    sys.exit(1)

# Validate quantity
if quantity != 100:
    print("Error: quantity must be 100 shares for this assignment")
    sys.exit(1)

# Validate price
if price <= 0:
    print("Error: price must be greater than 0")
    sys.exit(1)

# Build the order
order = {
    "username": username,
    "stock": stock,
    "side": side,
    "quantity": quantity,
    "price": price
}

message = json.dumps(order)

# Connect to RabbitMQ
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host=endpoint)
)
channel = connection.channel()

# Declare ORDERS exchange to act like a topic
channel.exchange_declare(exchange='orders', exchange_type='fanout')

# Publish the order
channel.basic_publish(
    exchange='orders',
    routing_key='',
    body=message
)

print("\n===== ORDER SENT =====")
print(f"Trader: {username}")
print(f"Stock: {stock}")
print(f"Side: {side}")
print(f"Quantity: {quantity}")
print(f"Price: {price}")
print("======================\n")

connection.close()