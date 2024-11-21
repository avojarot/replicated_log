# Replicated Log System
A simple replicated log system using Python's FastAPI, Docker, and Docker Compose. It consists of one Master server and multiple Secondary servers.

## Features
### Master Server [main.py](main.py):

Accepts messages via a POST request.
Replicates messages to all Secondary servers.
Waits for acknowledgments (blocking replication).
Provides a GET endpoint to retrieve all messages.
### Secondary Servers (secondary.py):

Receive and store replicated messages.
Simulate delay to demonstrate blocking behavior.
Provide a GET endpoint to retrieve stored messages.
## Quick Start
### Clone the Repository:

```
git clone https://github.com/yourusername/replicated-log.git
cd replicated-log
```
### Build and Run the Application:

```
docker-compose up --build
```
Master Server: http://localhost:8000

Secondary Servers:
Secondary 1: http://localhost:8001
Secondary 2: http://localhost:8002

## API Endpoints
### Master Server (http://localhost:8000)
#### POST /messages

Description: Add a message with a specified write_concern and replicate it to Secondaries.

Request Body:

```
{
  "content": "Your message here",
  "write_concern": 2
}

```
#### GET /messages

Description: Retrieve all messages.
### Secondary Servers (http://localhost:8001, http://localhost:8002)
#### GET /messages
Description: Retrieve replicated messages.

## Testing the Application
All commands to test are shown in [test_commands.sh](test_commands.sh)

## Notes
Blocking Replication: The Master waits for all Secondaries to acknowledge receipt before responding.

Artificial Delay: Secondaries use time.sleep() to simulate network latency.

Write Concern (write_concern): Allows clients to specify the number of acknowledgments required before the Master responds.

Artificial Delay: Secondaries introduce random delays to simulate network latency and test eventual consistency.

Blocking Replication: The Master waits for the specified number of acknowledgments, which may cause delays in responses.

Message Deduplication: Messages are deduplicated based on a unique message_id assigned by the Master.

Total Ordering: All nodes maintain the same order of messages based on message_id.

Logs: View logs with docker-compose logs -f. test logs are in file [Logs.txt](Logs.txt)