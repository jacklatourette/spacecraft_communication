from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from pydantic import ValidationError, field_validator
from sqlmodel import Field, Session, select

from scheduler.db import BaseModel, create_db_and_tables, engine
from data_ingestor.tasks import stream_data


class Scheduler(BaseModel, table=True):
    """Model for scheduled communications."""

    id: int | None = Field(default=None, primary_key=True)
    ship_name: str = Field(
        index=True, nullable=False, description="Name of the spaceship."
    )
    start_time: datetime = Field(
        nullable=False,
        gt=datetime.now(timezone.utc),
        description="Start time for scheduled communication.",
    )
    duration: int = Field(
        nullable=False, gt=0, description="The duration of the stream in seconds."
    )
    task_id: str | None = Field(
        default=None, description="Task ID for the scheduled communication."
    )

    @field_validator("start_time")
    @classmethod
    def validate_start_time(cls, value):
        """Validate that the start time is greater than the current time and converted to UTC"""
        value = value.astimezone(timezone.utc)
        if value < datetime.now(timezone.utc):
            raise ValueError("Start time must be greater than current time")
        else:
            return value


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Context manager for the FastAPI app."""
    # Startup event
    create_db_and_tables()
    # Yield control to the FastAPI app
    yield
    # Shutdown event


app = FastAPI(lifespan=lifespan)


@app.get("/healthcheck/", status_code=200)
def healthcheck():
    """Health check for the service."""
    return {"message": "Service is up and running."}


@app.post("/scheduler/", status_code=201)
def create_event(scheduler: Scheduler):
    """Create a scheduled communication"""
    try:
        Scheduler.model_validate(scheduler)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=f"{str(e)}")
    else:
        task = stream_data.apply_async(
            eta=scheduler.start_time,
            args=(scheduler.ship_name, scheduler.start_time, scheduler.duration),
        )
        scheduler.task_id = task.id
        with Session(engine) as session:
            session.add(scheduler)
            session.commit()
            session.refresh(scheduler)
        return scheduler


@app.get("/scheduler/", status_code=200)
def read_scheduler():
    """Read all scheduled communications"""
    with Session(engine) as session:
        schedule = session.exec(select(Scheduler)).all()
        return schedule
