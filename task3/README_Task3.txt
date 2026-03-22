RabbitMQ Contact Tracing System – Prototype 3

--------------------------------------------------

OVERVIEW

This project implements a contact tracing system using Python and RabbitMQ.

People move randomly in a 2D grid. When two people occupy the same position at the same time, a contact event is recorded.

Users can query a person to see who they have come into contact with. A GUI is provided to visualise the environment and perform queries.

--------------------------------------------------

COMPONENTS

person.py  
Simulates a person moving randomly and publishing positions.

tracker.py  
Central system that:
- Tracks positions
- Detects contacts
- Stores contact history
- Responds to queries

query.py  
Sends a query for a person and prints their contacts.

contact_gui.py  
Displays the grid, people positions, and allows querying contacts visually.

common.py  
Shared RabbitMQ messaging logic.

--------------------------------------------------

MIDDLEWARE

RabbitMQ uses one topic exchange:

tracking

Routing keys:
- position → person → tracker
- query → GUI/query → tracker
- query-response → tracker → GUI/query

--------------------------------------------------

REQUIREMENTS

- Python 3.x
- Docker Desktop running
- pika library

Install dependency:

pip install pika

--------------------------------------------------

STEP 1 – START RABBITMQ

docker ps -a

If container exists:
docker start rabbitmq

If not:
docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management

--------------------------------------------------

STEP 2 – NAVIGATE TO TASK 3

cd task3

--------------------------------------------------

STEP 3 – START TRACKER (MANDATORY FIRST)

Terminal 1:

python tracker.py localhost

--------------------------------------------------

STEP 4 – START PERSONS

Open separate terminals:

Terminal 2:
python person.py localhost Ana 1 10

Terminal 3:
python person.py localhost Luis 1 10

Arguments:
- localhost → RabbitMQ host
- Name → unique identifier
- 1 → movement interval (seconds)
- 10 → grid size

IMPORTANT:
At least 2 persons must be running for contacts to occur.

--------------------------------------------------

STEP 5 – RUN GUI

Terminal 4:

python contact_gui.py localhost 10

IMPORTANT:
The GUI WILL NOT start without both arguments.

--------------------------------------------------

STEP 6 – TEST SYSTEM

1. Wait until two people randomly meet (same position)
2. In GUI:
   - type a name (e.g. Ana)
   - click "Search Contacts"

OR use console:

python query.py localhost Ana

--------------------------------------------------

EXPECTED BEHAVIOUR

- People move continuously in the grid
- Positions update in real time
- When two people collide → contact is recorded
- Query returns contacts in reverse chronological order
- GUI displays:
  - current positions
  - contact results
  - environment grid

--------------------------------------------------

COMMON ISSUES

1. GUI not loading
→ Run with arguments:
  python contact_gui.py localhost 10

2. No contacts found
→ People have not collided yet
→ Wait longer

3. No movement visible
→ Ensure tracker.py is running
→ Ensure person.py processes are running

4. Query returns nothing
→ Check exact name (case-sensitive)

--------------------------------------------------

STOP APPLICATION

- Close GUI window
- Stop all terminals (Ctrl + C)

--------------------------------------------------

NOTES

- Contact detection only occurs when positions overlap
- System runs entirely in memory
- GUI shows current state and latest query results