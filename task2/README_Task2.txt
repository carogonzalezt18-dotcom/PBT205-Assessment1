PBT205 – Task 2: Trading System (RabbitMQ)

Overview
This project implements a simple trading system using RabbitMQ as middleware. 
It simulates an exchange where traders submit BUY and SELL orders for stocks, 
and the exchange matches orders based on price conditions.

System Components

1. sendOrder.py
A command-line application that sends an order to the system.

Usage:
python sendOrder.py <username> <endpoint> <stock> <side> <quantity> <price>

Example:
python sendOrder.py carolina localhost XYZ BUY 100 180

Rules:
- Side must be BUY or SELL
- Quantity must be exactly 100
- Price must be greater than 0


2. exchange.py
The core component of the system. It:
- Listens to incoming orders from the 'orders' exchange
- Maintains an in-memory order book
- Matches BUY and SELL orders
- Publishes executed trades to the 'trades' exchange

Matching Logic:
A trade occurs when:
Buyer price >= Seller price

Trade price is set to the seller's price.


3. tradeGUI.py
A simple graphical interface that displays:
- Latest trade price
- Buyer and seller information
- Stock symbol

Usage:
python tradeGUI.py localhost


System Architecture

sendOrder.py → (orders exchange) → exchange.py → (trades exchange) → tradeGUI.py

RabbitMQ is used with fanout exchanges to simulate topics:
- orders
- trades


How to Run

Step 1:
Start RabbitMQ (Docker must be running)

Step 2:
Open Terminal 1:
python exchange.py localhost

Step 3:
Open Terminal 2:
python tradeGUI.py localhost

Step 4:
Open Terminal 3:
Send orders:

python sendOrder.py carolina localhost XYZ BUY 100 180
python sendOrder.py juan localhost XYZ SELL 100 170

Expected Result:
- Exchange matches the orders
- Trade is executed
- GUI updates with latest trade price


Features Implemented

- Order validation (side, quantity, price)
- Order book management
- Matching logic (BUY vs SELL)
- Trade publishing
- GUI visualization
- Support for multiple stocks


Notes

- Only limit orders are supported (no market orders)
- Quantity is fixed to 100 shares as per assignment
- Order book is stored in memory (no persistence)
- GUI shows only the latest trade


