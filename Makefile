
deploy:
	docker compose up --scale worker=3;

deploy-scheduler:
	docker compose up scheduler;

deploy-spaceship:
	docker compose up spaceship;

deploy-ingestor:
	docker compose up worker;

undeploy:
	docker rm -f $(shell docker compose ps -aq);

get-ship-data:
	docker exec -it $(shell docker ps -q --filter name=scheduler) python3 /app/scripts/get_ship_data.py;
