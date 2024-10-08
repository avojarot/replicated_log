from fastapi import FastAPI
from pydantic import BaseModel
import time
import logging

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("secondary")

messages = []

class Message(BaseModel):
    content: str

@app.post("/replicate")
async def replicate_message(message: Message):
    # Introduce artificial delay to simulate blocking replication
    time.sleep(2)  # 2-second delay
    messages.append(message.content)
    logger.info(f"Replicated message: {message.content}")
    return {"message": "Message replicated"}

@app.get("/messages")
def get_messages():
    logger.info("Fetching all replicated messages")
    return {"messages": messages}
