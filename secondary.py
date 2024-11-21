from fastapi import FastAPI
from pydantic import BaseModel
import asyncio
import random
import logging

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("secondary")

messages = []
message_ids = set()
messages_lock = asyncio.Lock()
message_queue = []
processing = False

class Message(BaseModel):
    id: int
    content: str

async def process_messages():
    global processing
    if processing:
        return
    processing = True
    while message_queue:
        async with messages_lock:
            message = message_queue.pop(0)
        # Simulate delay
        delay = random.uniform(1, 5)  # Delay between 1 and 5 seconds
        await asyncio.sleep(delay)
        async with messages_lock:
            if message['id'] in message_ids:
                logger.info(f"Duplicate message detected: {message['id']}")
                continue
            messages.append(message)
            message_ids.add(message['id'])
        logger.info(f"Processed message {message['id']}: {message['content']}")
    processing = False

@app.post("/replicate")
async def replicate_message(message: Message):
    logger.info(f"Received replication request for message {message.id}")
    async with messages_lock:
        message_queue.append({"id": message.id, "content": message.content})
    asyncio.create_task(process_messages())
    return {"message": "ACK"}

@app.get("/messages")
async def get_messages():
    logger.info("Fetching all replicated messages")
    async with messages_lock:
        ordered_messages = sorted(messages, key=lambda x: x['id'])
        return {"messages": ordered_messages}
