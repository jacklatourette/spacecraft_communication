from datetime import datetime, timezone
import json
import logging
import random
import socket
from time import sleep
from uuid import uuid4

from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from threading import Event, Semaphore


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Keep track of the mutexes for each event key.
stop_stream_tracker = {}
# Semaphore to limit the number of concurrent streams.
streaming_semaphore = Semaphore(10)


class StartStream(BaseModel):
    """Model for starting a stream."""
    host: str
    port: int


app = FastAPI()


def generate_response_payload() -> dict:
    """Generate a random payload for streaming."""
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "description": "Battery Voltage",
        "value": random.randint(5, 30),
        "unit": "V",
    }


def streaming_task(stream_payload: StartStream, event_key: str):
    """Background task to stream data over udp to given host."""
    with streaming_semaphore:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        while not stop_stream_tracker[event_key].is_set():
            payload = json.dumps(generate_response_payload()).encode()
            try:
                sock.sendto(payload, (stream_payload.host, stream_payload.port))
            except Exception as e:
                logger.error(
                    f"Error while sending payload to {stream_payload.host}:{stream_payload.port}: {e}"
                )
        sock.close()
        stop_stream_tracker.pop(event_key)
        logger.info(f"Stream ended for {stream_payload.host}:{stream_payload.port}")


@app.get("/stream/")
async def get_stream():
    """Get the number of active streams."""
    return {"active_streams": stop_stream_tracker.keys()}


@app.post("/stream/")
async def start_stream(start_stream: StartStream, background_tasks: BackgroundTasks):
    """Start streaming data to a given host."""
    logger.info(f"Starting stream to {start_stream.host}:{start_stream.port}")
    event_key = str(uuid4())
    stop_stream_tracker[event_key] = Event()
    background_tasks.add_task(streaming_task, start_stream, event_key)
    return {"message": "Communication started", "event_key": event_key}


@app.delete("/stream/{stream_key}")
async def stop_stream(stream_key: str):
    """Stop streaming data of a given event_id."""
    if stream_key in stop_stream_tracker:
        stop_stream_tracker[stream_key].set()
        return {"message": "Communication stopped"}
    else:
        raise HTTPException(status_code=404, detail="Event key not found")


@app.get("/healthcheck/")
def healthcheck():
    """Health check for the service."""
    return {"message": "Service is up and running."}
