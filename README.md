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
Message Handling: Accepts messages with a specified write concern (write_concern), assigns sequential message_ids, and stores them locally.

Write Concern: Clients specify the number of acknowledgments (w) required before the Master responds.

Replication with Retry: Replicates messages to healthy Secondaries; retries failed replications in the background.

Heartbeat Mechanism: Periodically checks the health of Secondary servers.

Quorum Handling: Switches to read-only mode if quorum is lost; resumes normal operations when restored.

#### Endpoints:
POST /messages: Add a message with write concern.

GET /messages: Retrieve all messages.

GET /health: Get health status of Secondaries.
### Secondary Servers (http://localhost:8001, http://localhost:8002)
Message Processing: Receives replicated messages, processes them in total order based on message_id.

Error Simulation: Randomly simulates errors and delays to test the Master's retry and deduplication logic.
#### Endpoints:
POST /replicate: Receive messages from the Master.
GET /messages: Retrieve stored messages.
GET /status: Provide health status for heartbeat checks.
## Testing the Application
All commands to test are shown in [test_commands.sh](test_commands.sh)

## Notes
Write Concern: Ensures messages are acknowledged by a specified number of nodes for consistency.

Retry Mechanism: Failed replications are retried in the background until successful.

Total Ordering: Messages are processed in the same order across all nodes based on message_id.

Heartbeat Checks: Master monitors the health of Secondaries to adjust replication strategies.

Quorum Handling: Master enters read-only mode if a majority of nodes are unavailable.

Logs: View logs with docker-compose logs -f. test logs are in file [Logs.txt](Logs.txt)