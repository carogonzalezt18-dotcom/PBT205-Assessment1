import pika
import json
import sys
import threading
import tkinter as tk


# Check command-line arguments
if len(sys.argv) != 2:
    print("Usage: python tradeGUI.py <endpoint>")
    sys.exit(1)

endpoint = sys.argv[1]

window = tk.Tk()
window.title("Trading System - Latest Trade")
window.geometry("500x300")
window.configure(bg="#f4f4f4")

title_label = tk.Label(
    window,
    text="Latest Trade Information",
    font=("Arial", 18, "bold"),
    bg="#f4f4f4"
)
title_label.pack(pady=15)

stock_label = tk.Label(
    window,
    text="Stock: XYZ",
    font=("Arial", 14),
    bg="#f4f4f4"
)
stock_label.pack()

price_label = tk.Label(
    window,
    text="No trades yet",
    font=("Arial", 28, "bold"),
    fg="#1a4d8f",
    bg="#f4f4f4"
)
price_label.pack(pady=20)

details_label = tk.Label(
    window,
    text="Waiting for trade data...",
    font=("Arial", 12),
    bg="#f4f4f4"
)
details_label.pack(pady=10)


def update_gui(trade):
    stock_label.config(text=f"Stock: {trade['stock']}")
    price_label.config(text=f"${trade['trade_price']}")
    details_label.config(
        text=f"Buyer: {trade['buyer']} | Seller: {trade['seller']} | Qty: {trade['quantity']}"
    )


def consume_trades():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=endpoint)
    )
    channel = connection.channel()

    # Declare trades exchange
    channel.exchange_declare(exchange='trades', exchange_type='fanout')

    # Create a temporary queue for this GUI instance
    result = channel.queue_declare(queue='', exclusive=True)
    trades_queue = result.method.queue
    channel.queue_bind(exchange='trades', queue=trades_queue)

    def callback(ch, method, properties, body):
        try:
            trade = json.loads(body.decode())
            window.after(0, update_gui, trade)
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            print(f"Error in GUI listener: {e}")
            ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_qos(prefetch_count=1)

    channel.basic_consume(
        queue=trades_queue,
        on_message_callback=callback,
        auto_ack=False
    )

    channel.start_consuming()


listener_thread = threading.Thread(target=consume_trades, daemon=True)
listener_thread.start()

window.mainloop()