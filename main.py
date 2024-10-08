from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
import httpx
import logging

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("master")

messages = []

# List of Secondary server URLs (service names in Docker Compose)
SECONDARIES = [
    "http://secondary1:8000",
    "http://secondary2:8000",
]

class Message(BaseModel):
    content: str

@app.post("/messages")
async def add_message(message: Message):
    messages.append(message.content)
    logger.info(f"Received message: {message.content}")
    async def replicate_to_secondary(secondary_url):
        try:
            async with httpx.AsyncClient() as client:
                replicate_url = f"{secondary_url}/replicate"
                logger.info(f"Replicating to {replicate_url}")
                response = await client.post(replicate_url, json=message.dict())
                response.raise_for_status()
                logger.info(f"Received ACK from {secondary_url}")
        except Exception as e:
            logger.error(f"Failed to replicate to {secondary_url}: {e}")
            raise

    tasks = [replicate_to_secondary(url) for url in SECONDARIES]
    try:
        await asyncio.gather(*tasks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"message": "Message added and replicated to all Secondaries."}

@app.get("/messages")
def get_messages():
    logger.info("Fetching all messages")
    return {"messages": messages}
