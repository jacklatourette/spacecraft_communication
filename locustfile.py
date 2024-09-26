from datetime import datetime, timedelta, timezone
from locust import HttpUser, task, between
import random

random_names = [
    "USS Enterprise",
    "Millennium Falcon",
    "Serenity",
    "Battlestar Galactica",
    "Event Horizon",
    "Red Dwarf",
    "Heart of Gold",
    "Rocinante",
    "TARDIS",
    "Planet Express",
]

class QuickstartUser(HttpUser):
    wait_time = between(1, 5)

    @task
    def create_scheduler(self):
        payload = {
            "ship_name": random.choice(random_names),
            "start_time": (datetime.now(timezone.utc) + timedelta(seconds=random.randint(10,60))).isoformat(),
            "duration": random.randint(10, 60),
        }
        self.client.post("/scheduler/", json=payload)
    
    @task
    def get_scheduler(self):
        self.client.get("/scheduler/")