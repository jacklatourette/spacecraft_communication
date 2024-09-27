# Spaceship Scheduler Streamer
Simulation of communicating with a spacecraft separated into scheduler, spaceship, and data ingestors. 

## How to run
The entire system is orchestrated in a docker compose file. To start run:
`make deploy`
This will run all parts. To run individual containers run either:
`make deploy-scheduler`
`make deploy-spaceship`
`make deploy-ingestor`

## How to test
First deploy the project with `make deploy`. The docker compose deployment includes a testing tool called Locust. In your browser navigate to (http://localhost:8089/) for the locust UI. Click the **New** button in the top right. Enter the number of users and **http://scheduler:8000** as the host. Click **stop** when you are satisfied with the number of calls. To review the number of messages saved by the *ingestor* by running `make get-ship-data`. To monitor the message bus you can navigate to RabbitMQ's UI here (http://localhost:15672/). There is also a Postman file in the root of the project.

## Scheduler 
The scheduler is a FastAPI service that stores the given schedules into a postgres instance with SQLModel, then pushes a task to celery with the task's eta the given start time. It uses a SQLModel model with pydantic style validation to verify the payload (if a more precise duration was required than seconds, I would keep it an int). 

## Spaceship
The spaceship is another FastAPI service that will spin off background processes that will stream randomly generated battery data to a given UDP host and port. These background processes use AnyIO threading to allow blocking calls to run continuously in the background. There is an additional endpoint added to provide the number of active streams (get /stream/).

## Data Ingestor
The work of opening UDP sockets, receiving data, and writing it to a database is being done with Celery tasks. With RabbitMQ as the message bus, the stream data task is picked up by one of three celery workers (specified in the Makefile). It is writing everything to Redis lists based on the given ship's name.   

## What I would add
- **Tests** and **More Validation on Payloads**
- First the celery workers could be run with the --concurrency flag set higher, the limiting factor was setting the different tasks to open different ports which could have been done with a shared lock created in Redis with redis-lock-py. 
- Redis though known for its speed, being an in memory database, but I would experiment with other doc stores like MongoDB or DynamoDB for their resiliency.
- Adding a settings.yml file for each service to hold hosts and constants would be useful if this needed to be deployed into different environments.
- They each should have separate requirements.txt to minimize the size of their docker images.

