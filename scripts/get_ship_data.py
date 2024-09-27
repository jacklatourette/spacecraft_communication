import redis


redis_client = redis.StrictRedis(host="redis", port=6379, db=1)


def get_ship_data():
    """Get the data of the spaceship."""
    keys = redis_client.keys()
    for key in keys:
        values = redis_client.lrange(key, 0, -1)
        print(f"{key.decode()}: {len(values)}")


if __name__ == "__main__":
    get_ship_data()
