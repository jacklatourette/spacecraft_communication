from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, create_engine

# Define your database URL
postgres_url = "postgresql://postgres:postgres@db:5432/scheduler"

# connect_args = {"check_same_thread": False}
engine = create_engine(postgres_url, echo=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# Create a base class for your models
class BaseModel(SQLModel):
    class Config:
        orm_mode = True
        anystr_strip_whitespace = True

# Generate a session
def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()