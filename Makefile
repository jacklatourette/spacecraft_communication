
deploy:
	docker-compose up -d --scale worker=3;

undeploy:
	docker rm -f $(shell docker ps -a -q);

get-ship-data:
	docker exec -it $(shell docker ps -q --filter name=scheduler) python3 /app/scripts/get_ship_data.py;
