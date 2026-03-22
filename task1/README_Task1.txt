RabbitMQ Chat Application – Prototype 1

--------------------------------------------------

OVERVIEW

This prototype implements a real-time chat system using Python and RabbitMQ.

Users can join a chat room and exchange messages. Messages are isolated per room, ensuring only users in the same room receive them.

--------------------------------------------------

ARCHITECTURE

- RabbitMQ is used as the message broker
- Each chat room is implemented as a RabbitMQ exchange (fanout)
- Each user creates a temporary queue and binds it to the room exchange
- Messages are broadcast to all users in the same room

--------------------------------------------------

REQUIREMENTS

- Python 3.x
- Docker Desktop (running)
- Python library: pika

Install dependency:

pip install pika



--------------------------------------------------

STEP 1 – START RABBITMQ

Check existing containers:

docker ps -a

If container exists:

docker start rabbitmq

If not:

docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management

Dashboard:
http://localhost:15672  
Username: guest  
Password: guest  

--------------------------------------------------

STEP 2 – NAVIGATE TO PROJECT

IMPORTANT:

Navigate into the task1 folder before running scripts:

cd task1

--------------------------------------------------

STEP 3 – RUN CHAT APPLICATION

Run:

python chat_gui.py

Open multiple terminals to simulate multiple users.

--------------------------------------------------

STEP 4 – JOIN A CHAT ROOM

Example:

User 1:
Username: caro  
Port: 5672  
Room: music  

User 2:
Username: will  
Port: 5672  
Room: music  

--------------------------------------------------

STEP 5 – TEST MESSAGING

- Send messages between users
- Verify both users receive them in real time

--------------------------------------------------

STEP 6 – TEST ROOM ISOLATION

Open a third instance:

python chat_gui.py

User 3:
Room: futbol

Verify:
- Messages from "music" do NOT appear in "futbol"
- Messages from "futbol" do NOT appear in "music"

--------------------------------------------------

APPLICATION BEHAVIOUR

- "Send" sends a message
- "Exit" returns to login screen
- Closing the window (X) fully exits the application

--------------------------------------------------

STOP APPLICATION

- Close all windows
- Stop container if needed:

Ctrl + C

--------------------------------------------------

COMMON ISSUES

1. File not found
→ Ensure you are inside the "task1" folder

2. Connection error
→ Check Docker is running
→ Check RabbitMQ container is active

3. Messages not received
→ Ensure same room name (case-sensitive)

4. GUI does not close properly
→ Fixed in latest version (uses root.destroy)

--------------------------------------------------

NOTES

- GUI is the main interface
- Backend uses RabbitMQ messaging
- Demonstrates real-time communication and room isolation