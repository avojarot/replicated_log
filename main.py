from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import asyncio
import httpx
import logging

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("master")

messages = []
message_ids = set()
message_counter = 0
messages_lock = asyncio.Lock()

SECONDARIES = [
    "http://secondary1:8000",
    "http://secondary2:8000",
    # Additional secondaries can be added dynamically
]

# Heartbeat statuses
secondary_statuses = {}
heartbeat_interval = 5  # seconds

# Pending replications
pending_replications = {}
for url in SECONDARIES:
    pending_replications[url] = set()

class Message(BaseModel):
    content: str
    write_concern: int = Field(..., ge=1)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(heartbeat_monitor())
    asyncio.create_task(retry_pending_replications())

@app.post("/messages")
async def add_message(message: Message):
    global message_counter
    write_concern = message.write_concern
    total_nodes = 1 + len(SECONDARIES)  # Master + Secondaries
    quorum = (total_nodes // 2) + 1

    if write_concern > total_nodes:
        raise HTTPException(status_code=400, detail=f"write_concern cannot be greater than {total_nodes}")

    # Get list of healthy secondaries
    healthy_secondaries = [s for s in SECONDARIES if secondary_statuses.get(s, 'unhealthy') == 'healthy']
    available_nodes = 1 + len(healthy_secondaries)

    if available_nodes < quorum:
        raise HTTPException(status_code=503, detail="Quorum not met. Master is in read-only mode.")

    if write_concern > available_nodes:
        raise HTTPException(status_code=503, detail="Not enough healthy nodes to meet write_concern.")

    async with messages_lock:
        message_counter += 1
        message_id = message_counter
        if message_id in message_ids:
            logger.info(f"Duplicate message detected: {message_id}")
            return {"message": "Duplicate message ignored."}
        messages.append({"id": message_id, "content": message.content})
        message_ids.add(message_id)

    logger.info(f"Received message: {message.content} with write_concern={write_concern}")

    # Only replicate to healthy secondaries
    tasks = [replicate_to_secondary(url, message_id, message.content) for url in healthy_secondaries]

    # Collect ACKs
    ack_count = 1  # ACK from Master itself

    if tasks:
        try:
            done, pending = await asyncio.wait(tasks, timeout=5)
            for task in done:
                result = task.result()
                if result is True:
                    ack_count += 1
        except Exception as e:
            logger.error(f"Error during replication: {e}")

    if ack_count >= write_concern:
        logger.info(f"Required ACKs received: {ack_count}/{write_concern}")
        return {"message": "Message added and replicated.", "acks": ack_count}
    else:
        logger.error(f"Not enough ACKs received: {ack_count}/{write_concern}")
        raise HTTPException(status_code=500, detail="Not enough acknowledgments received.")

@app.get("/messages")
async def get_messages():
    logger.info("Fetching all messages")
    async with messages_lock:
        return {"messages": list(messages)}

@app.get("/health")
async def get_health():
    return {"statuses": secondary_statuses}

async def heartbeat_monitor():
    while True:
        for secondary_url in SECONDARIES:
            try:
                async with httpx.AsyncClient() as client:
                    health_url = f"{secondary_url}/status"
                    response = await client.get(health_url, timeout=2)
                    if response.status_code == 200:
                        secondary_statuses[secondary_url] = 'healthy'
                    else:
                        secondary_statuses[secondary_url] = 'unhealthy'
            except Exception:
                secondary_statuses[secondary_url] = 'unhealthy'
            logger.info(f"Heartbeat check for {secondary_url}: {secondary_statuses[secondary_url]}")
        await asyncio.sleep(heartbeat_interval)

async def replicate_to_secondary(secondary_url, message_id, message_content):
    payload = {"id": message_id, "content": message_content}

    if secondary_statuses.get(secondary_url, 'unhealthy') == 'unhealthy':
        logger.info(f"{secondary_url} is unhealthy. Skipping replication for now.")
        # Add to pending replications
        async with messages_lock:
            pending_replications[secondary_url].add(message_id)
        return False

    try:
        async with httpx.AsyncClient() as client:
            replicate_url = f"{secondary_url}/replicate"
            logger.info(f"Replicating to {replicate_url}")
            response = await client.post(replicate_url, json=payload, timeout=5)
            response.raise_for_status()
            logger.info(f"Received ACK from {secondary_url} for message {message_id}")
            return True
    except Exception as e:
        logger.error(f"Failed to replicate to {secondary_url}: {e}")
        # Mark the secondary as unhealthy
        secondary_statuses[secondary_url] = 'unhealthy'
        # Add to pending replications
        async with messages_lock:
            pending_replications[secondary_url].add(message_id)
        return False

async def retry_pending_replications():
    while True:
        for secondary_url in SECONDARIES:
            pending_messages = pending_replications.get(secondary_url, set())
            if not pending_messages:
                continue
            if secondary_statuses.get(secondary_url, 'unhealthy') == 'unhealthy':
                continue
            messages_to_replicate = []
            async with messages_lock:
                for message_id in sorted(pending_messages):
                    # Get the message content
                    message = next((m for m in messages if m['id'] == message_id), None)
                    if message:
                        messages_to_replicate.append((message_id, message['content']))

            for message_id, message_content in messages_to_replicate:
                # Attempt replication
                success = await replicate_to_secondary(secondary_url, message_id, message_content)
                if success:
                    # Remove from pending_replications
                    async with messages_lock:
                        pending_replications[secondary_url].discard(message_id)
        await asyncio.sleep(heartbeat_interval)
