RabbitMQ Chat Application – Prototype 1

--------------------------------------------------

OVERVIEW

This prototype implements a simple real-time chat system using Python and RabbitMQ.

Users can join a chat room and exchange messages in real time. The system ensures that messages are only delivered to users within the same room (message isolation).

--------------------------------------------------

ARCHITECTURE

- RabbitMQ is used as the message broker
- Each chat room is implemented as a queue
- Users publish messages to a specific room
- Only users subscribed to that room receive the messages

--------------------------------------------------

REQUIREMENTS

- Python 3.x
- Docker Desktop (running)
- Python library: pika

Install dependency:

pip install pika

--------------------------------------------------

STEP 1 – START RABBITMQ

IMPORTANT:
If RabbitMQ is already running, DO NOT run a new container.

Check existing containers:

docker ps -a

If a RabbitMQ container already exists:

docker start rabbitmq

If no container exists, create one:

docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management

RabbitMQ Dashboard:
http://localhost:15672
Username: guest
Password: guest

--------------------------------------------------

STEP 2 – TEST CONNECTION (OPTIONAL)

Run:

python task1/test_connection.py

Expected output:

Connected successfully to RabbitMQ!

--------------------------------------------------

STEP 3 – RUN CHAT APPLICATION

Open a terminal and run:

python task1/chat_gui.py

Repeat this command in another terminal to open multiple users.

--------------------------------------------------

STEP 4 – JOIN A CHAT ROOM

Example:

User 1:
Username: caro
Port: 5672
Room: music

User 2: 
Username: Will
Port: 5672
Room: music

Click "Join Chat" in both windows.

--------------------------------------------------

STEP 5 – TEST MESSAGING

- Send a message from one user
- Verify that it appears in both chat windows

--------------------------------------------------

STEP 6 – TEST ROOM ISOLATION (IMPORTANT)

Open a third terminal:

python task1/chat_gui.py

User 3:
Username: Pablo
Port: 5672
Room: futbol

Test:

- Send messages in "music"
- Verify they do NOT appear in "futbol"

- Send messages in "futbol"
- Verify they do NOT appear in "music"

This confirms correct message isolation between rooms.

--------------------------------------------------

HOW IT WORKS

- Each room corresponds to a RabbitMQ queue
- Messages are published to the queue of that room
- All users connected to that room receive the messages
- Users in different rooms do not receive those messages

--------------------------------------------------

STOP APPLICATION

- Close all chat windows
- Stop RabbitMQ container if needed:

Ctrl + C

--------------------------------------------------

COMMON ISSUES

1. Connection error
- Ensure Docker is running
- Ensure RabbitMQ container is active
- Use port 5672

2. Messages not received
- Verify both users are in the same room
- Check spelling of room names (case-sensitive)

3. Port already in use
- RabbitMQ is already running
- Use "docker start rabbitmq" instead of creating a new container

--------------------------------------------------

NOTES

- The GUI is the main interface for this prototype
- Backend communication is handled via RabbitMQ queues
- This prototype demonstrates real-time messaging and room isolation