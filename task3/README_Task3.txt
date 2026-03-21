RabbitMQ Contact Tracing System – Prototype 3

--------------------------------------------------

OVERVIEW

This prototype implements a contact tracing system using Python and RabbitMQ.

The system simulates a 2D environment (grid) where multiple people move randomly. When two people occupy the same position at the same time, a "contact event" is recorded.

Users can query the system to retrieve a list of people they have come into contact with.

A graphical user interface (GUI) is provided to visualize the environment and perform queries.

--------------------------------------------------

ARCHITECTURE

The system consists of four main components:

1. PERSON (person.py)
   - Simulates a user moving in a 2D grid
   - Publishes position updates to RabbitMQ

2. TRACKER (tracker.py)
   - Subscribes to position updates
   - Maintains current positions of all users
   - Detects contact events (same position, same time)
   - Stores contact history
   - Responds to queries

3. QUERY (query.py)
   - Sends a request for a specific user
   - Receives contact history from tracker

4. GUI (contact_gui.py)
   - Displays the environment grid
   - Shows real-time positions
   - Highlights collisions
   - Allows user queries

--------------------------------------------------

MIDDLEWARE (RABBITMQ TOPICS)

The system uses three queues:

- position
  Receives movement updates from all users

- query
  Receives requests for contact history

- query-response
  Sends back the results of queries

--------------------------------------------------

REQUIREMENTS

- Python 3.x
- Docker Desktop (running)
- pika library

Install dependency:

pip install pika

--------------------------------------------------

STEP 1 – START RABBITMQ

Check existing containers:

docker ps -a

If RabbitMQ exists:

docker start rabbitmq

If not:

docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management

--------------------------------------------------

STEP 2 – START TRACKER

Open a terminal:

python task3/tracker.py localhost

Expected output:

Tracker is running...
Waiting for position and query messages...

--------------------------------------------------

STEP 3 – START PERSON SIMULATIONS

Open two separate terminals:

Example:

python task3/person.py localhost Ana 1 10
python task3/person.py localhost Luis 1 10

Arguments:
- localhost → RabbitMQ host
- Name → unique identifier
- Speed → movement interval (seconds)
- Grid size → e.g. 10 for 10x10

--------------------------------------------------

STEP 4 – VERIFY CONTACT DETECTION

When two users occupy the same position:

Expected output in tracker:

[CONTACT] Ana met Luis at (x, y) at time

--------------------------------------------------

STEP 5 – RUN QUERY (CONSOLE)

Open another terminal:

python task3/query.py localhost Ana

Expected output:

Contacts for Ana:
- Luis

--------------------------------------------------

STEP 6 – RUN GUI

Run:

python task3/contact_gui.py

Features:
- Visual grid environment
- Real-time position updates
- Collision highlighting (red markers)
- Query input field
- Contact results display

--------------------------------------------------

STEP 7 – TEST FUNCTIONALITY

1. Start tracker
2. Start at least 2 persons
3. Wait for collision
4. Perform query in GUI or console

Expected behavior:
- Contacts appear after collision
- Results show in reverse chronological order
- Positions update continuously

--------------------------------------------------

HOW IT WORKS

- Each person publishes their position to RabbitMQ
- Tracker listens to all updates
- If two users share the same coordinates at the same time:
  → A contact event is recorded
- Contacts are stored per user
- Queries retrieve contact history from tracker
- GUI subscribes to updates and displays environment visually

--------------------------------------------------

BOUNDARY CONDITIONS

- Grid size is configurable (default 10x10)
- Users cannot move outside grid boundaries
- Movement is random (similar to chess king moves)

--------------------------------------------------

STOP APPLICATION

- Close GUI
- Stop all terminals
- Stop RabbitMQ:

Ctrl + C

--------------------------------------------------

COMMON ISSUES

1. Connection error
- Ensure RabbitMQ is running
- Use localhost and port 5672

2. No contacts found
- Users have not collided yet
- Wait for overlap in positions

3. GUI not updating
- Ensure tracker is running
- Ensure persons are active

--------------------------------------------------

NOTES

- This system demonstrates asynchronous communication using RabbitMQ
- Contact tracing is based on real-time positional overlap
- GUI enhances usability and visualization of system state
