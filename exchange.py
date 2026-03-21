import pika
import json
import sys
from collections import defaultdict
from datetime import datetime


def timestamp():
    return datetime.now().strftime("%H:%M:%S")


def log_section(title):
    print(f"\n===== {title} =====")


def print_order_book(order_book):
    log_section("ORDER BOOK STATE")
    for stock, books in order_book.items():
        print(f"Stock: {stock}")
        print(f"  BUY : {books['BUY']}")
        print(f"  SELL: {books['SELL']}")
    print("============================\n")


def validate_order(order):
    required_fields = ["username", "stock", "side", "quantity", "price"]

    for field in required_fields:
        if field not in order:
            return False, f"Missing field: {field}"

    if order["side"] not in ["BUY", "SELL"]:
        return False, "Invalid side. Must be BUY or SELL."

    if not isinstance(order["quantity"], int):
        return False, "Quantity must be an integer."

    if order["quantity"] != 100:
        return False, "Quantity must be 100 shares for this assignment."

    if not isinstance(order["price"], (int, float)):
        return False, "Price must be numeric."

    if order["price"] <= 0:
        return False, "Price must be greater than 0."

    return True, "Valid order"


def try_match(order, order_book):
    stock = order["stock"]
    side = order["side"]

    if side == "BUY":
        opposite_orders = order_book[stock]["SELL"]

        for sell_order in opposite_orders:
            if order["price"] >= sell_order["price"]:
                print(f"[{timestamp()}] Matching condition met:")
                print(f"Buyer price >= Seller price -> {order['price']} >= {sell_order['price']}")

                opposite_orders.remove(sell_order)

                trade = {
                    "buyer": order["username"],
                    "seller": sell_order["username"],
                    "stock": stock,
                    "quantity": order["quantity"],
                    "trade_price": sell_order["price"]
                }
                return trade

        order_book[stock]["BUY"].append(order)
        return None

    elif side == "SELL":
        opposite_orders = order_book[stock]["BUY"]

        for buy_order in opposite_orders:
            if buy_order["price"] >= order["price"]:
                print(f"[{timestamp()}] Matching condition met:")
                print(f"Buyer price >= Seller price -> {buy_order['price']} >= {order['price']}")

                opposite_orders.remove(buy_order)

                trade = {
                    "buyer": buy_order["username"],
                    "seller": order["username"],
                    "stock": stock,
                    "quantity": order["quantity"],
                    "trade_price": order["price"]
                }
                return trade

        order_book[stock]["SELL"].append(order)
        return None

    return None


# Check command-line arguments
if len(sys.argv) != 2:
    print("Usage: python exchange.py <endpoint>")
    sys.exit(1)

endpoint = sys.argv[1]

# Order book structure by stock
order_book = defaultdict(lambda: {"BUY": [], "SELL": []})

# Connect to RabbitMQ
connection = pika.BlockingConnection(
    pika.ConnectionParameters(host=endpoint)
)
channel = connection.channel()

# Declare exchanges
channel.exchange_declare(exchange='orders', exchange_type='fanout')
channel.exchange_declare(exchange='trades', exchange_type='fanout')

# Create a temporary queue for the exchange and bind it to the orders exchange
result = channel.queue_declare(queue='', exclusive=True)
orders_queue = result.method.queue
channel.queue_bind(exchange='orders', queue=orders_queue)

print("Exchange is waiting for orders...")


def callback(ch, method, properties, body):
    try:
        order = json.loads(body.decode())

        log_section("NEW ORDER RECEIVED")
        print(f"[{timestamp()}] Trader : {order.get('username', 'UNKNOWN')}")
        print(f"[{timestamp()}] Stock  : {order.get('stock', 'UNKNOWN')}")
        print(f"[{timestamp()}] Side   : {order.get('side', 'UNKNOWN')}")
        print(f"[{timestamp()}] Qty    : {order.get('quantity', 'UNKNOWN')}")
        print(f"[{timestamp()}] Price  : {order.get('price', 'UNKNOWN')}")

        valid, message = validate_order(order)
        if not valid:
            log_section("ORDER REJECTED")
            print(f"[{timestamp()}] Reason: {message}")
            print("=========================\n")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        trade = try_match(order, order_book)

        if trade:
            trade_message = json.dumps(trade)

            channel.basic_publish(
                exchange='trades',
                routing_key='',
                body=trade_message
            )

            log_section("TRADE EXECUTED")
            print(f"[{timestamp()}] Buyer      : {trade['buyer']}")
            print(f"[{timestamp()}] Seller     : {trade['seller']}")
            print(f"[{timestamp()}] Stock      : {trade['stock']}")
            print(f"[{timestamp()}] Quantity   : {trade['quantity']}")
            print(f"[{timestamp()}] Trade Price: {trade['trade_price']}")
            print("=========================\n")
        else:
            log_section("NO MATCH FOUND")
            print(f"[{timestamp()}] Order added to order book.")
            print("======================\n")

        print_order_book(order_book)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except json.JSONDecodeError:
        log_section("ERROR")
        print(f"[{timestamp()}] Invalid JSON received.")
        print("================\n")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        log_section("UNEXPECTED ERROR")
        print(f"[{timestamp()}] {e}")
        print("========================\n")
        ch.basic_ack(delivery_tag=method.delivery_tag)


channel.basic_qos(prefetch_count=1)

channel.basic_consume(
    queue=orders_queue,
    on_message_callback=callback,
    auto_ack=False
)

channel.start_consuming()