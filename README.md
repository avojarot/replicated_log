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

Description: Add a message and replicate it.

Request Body:

```
{
  "content": "Your message here"
}
```
#### GET /messages

Description: Retrieve all messages.
### Secondary Servers (http://localhost:8001, http://localhost:8002)
#### GET /messages
Description: Retrieve replicated messages.

## Testing the Application
Add a Message:

```
curl.exe -X POST -H "Content-Type: application/json" -d "{\"content\": \"Hello, World!\"}" http://localhost:8000/messages
Retrieve Messages:
```
From Master:

```
curl.exe http://localhost:8000/messages
```
From Secondary 1:

```
curl.exe http://localhost:8001/messages
```
From Secondary 2:

```
curl.exe http://localhost:8002/messages
```

## Notes
Blocking Replication: The Master waits for all Secondaries to acknowledge receipt before responding.

Artificial Delay: Secondaries use time.sleep() to simulate network latency.

Logs: View logs with docker-compose logs -f. test logs are in file [Logs.txt](Logs.txt)