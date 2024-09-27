from datetime import datetime, timedelta, timezone
import logging
from os import environ
import redis
import requests
import socket

from celery import Celery
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = Celery("tasks", broker="pyamqp://user:password@rabbitmq:5672//")
redis_client = redis.StrictRedis(host="redis", port=6379, db=1)
udp_port = 1001


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
    retry=retry_if_exception_type(requests.RequestException),
)
def start_stream(port: int) -> str:
    """Start streaming data to a given host."""
    host = environ.get("HOSTNAME")
    response = requests.post(
        "http://spaceship:8001/stream/",
        json={"host": f"{host}", "port": port},
    )
    response.raise_for_status()
    return response.json()["event_key"]


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
    retry=retry_if_exception_type(requests.RequestException),
)
def stop_stream(stream_key: str):
    """Stop streaming data of a given event_id."""
    response = requests.delete(
        f"http://spaceship:8001/stream/{stream_key}",
    )
    response.raise_for_status()


@app.task()
def healthcheck():
    """Perform a health check on the services."""
    response = requests.get("http://spaceship:8001/healthcheck/")
    response.raise_for_status()
    redis_client.set("test_key", "test_value")
    redis_client.get("test_key")
    redis_client.delete("test_key")
    logger.info("Health Check Complete!")


@app.task()
def stream_data(ship_name: str, start_time: str, duration: int):
    """Stream data to a given host over UDP."""
    logger.info(f"Streaming data from {ship_name}")
    start_time = datetime.fromisoformat(start_time)

    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    udp_socket.bind(("0.0.0.0", udp_port))
    udp_socket.settimeout(5)
    stream_key = start_stream(udp_port)
    while datetime.now(timezone.utc) < start_time + timedelta(seconds=int(duration)):
        # Receive data from the UDP socket.
        data, _ = udp_socket.recvfrom(1024)
        decoded_data = data.decode("utf-8")
        redis_client.rpush(
            ship_name, decoded_data
        )  # Append the data to a Redis list 'udp_packets'
    stop_stream(stream_key)
    udp_socket.close()
    logger.info(f"Streaming data from {ship_name} completed.")
