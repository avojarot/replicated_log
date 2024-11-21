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
]

class Message(BaseModel):
    content: str
    write_concern: int = Field(..., ge=1)

@app.post("/messages")
async def add_message(message: Message):
    global message_counter
    write_concern = message.write_concern
    total_nodes = 1 + len(SECONDARIES)  # Master + Secondaries

    if write_concern > total_nodes:
        raise HTTPException(status_code=400, detail=f"write_concern cannot be greater than {total_nodes}")

    async with messages_lock:
        message_counter += 1
        message_id = message_counter
        if message_id in message_ids:
            logger.info(f"Duplicate message detected: {message_id}")
            return {"message": "Duplicate message ignored."}
        messages.append({"id": message_id, "content": message.content})
        message_ids.add(message_id)

    logger.info(f"Received message: {message.content} with write_concern={write_concern}")

    # Replicate to Secondaries
    async def replicate_to_secondary(secondary_url):
        try:
            async with httpx.AsyncClient() as client:
                replicate_url = f"{secondary_url}/replicate"
                payload = {"id": message_id, "content": message.content}
                logger.info(f"Replicating to {replicate_url}")
                response = await client.post(replicate_url, json=payload)
                response.raise_for_status()
                logger.info(f"Received ACK from {secondary_url}")
                return True
        except Exception as e:
            logger.error(f"Failed to replicate to {secondary_url}: {e}")
            return False

    tasks = [replicate_to_secondary(url) for url in SECONDARIES]
    ack_count = 1  # ACK from Master itself

    # Collect ACKs
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for result in results:
        if result is True:
            ack_count += 1

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
