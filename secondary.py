from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
import random
import logging

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("secondary")

messages = {}
message_ids = set()
messages_lock = asyncio.Lock()
message_queue = []
processing = False
expected_message_id = 1  # Start from 1

class Message(BaseModel):
    id: int
    content: str

@app.get("/status")
async def get_status():
    return {"status": "healthy"}

async def process_messages():
    global processing, expected_message_id
    if processing:
        return
    processing = True
    while True:
        async with messages_lock:
            if not message_queue:
                break
            message = message_queue[0]
            if message['id'] != expected_message_id:
                # Wait for the expected message ID
                await asyncio.sleep(1)
                continue
            message_queue.pop(0)

        # Simulate delay and random server error
        delay = random.uniform(1, 5)  # Delay between 1 and 5 seconds
        await asyncio.sleep(delay)
        if random.choice([True, False, False]):  # 33% chance to simulate error
            logger.error(f"Simulating server error for message {message['id']}")
            raise HTTPException(status_code=500, detail="Simulated server error")

        async with messages_lock:
            if message['id'] in message_ids:
                logger.info(f"Duplicate message detected: {message['id']}")
            else:
                messages[message['id']] = message
                message_ids.add(message['id'])
                expected_message_id += 1
                logger.info(f"Processed message {message['id']}: {message['content']}")
    processing = False

@app.post("/replicate")
async def replicate_message(message: Message):
    logger.info(f"Received replication request for message {message.id}")
    async with messages_lock:
        if message.id in message_ids:
            logger.info(f"Duplicate message received: {message.id}")
            return {"message": "ACK"}
        message_queue.append({"id": message.id, "content": message.content})
    asyncio.create_task(process_messages())
    return {"message": "ACK"}

@app.get("/messages")
async def get_messages():
    logger.info("Fetching all replicated messages")
    async with messages_lock:
        # Return messages in order
        ordered_messages = [messages[i] for i in sorted(messages.keys())]
        return {"messages": ordered_messages}
