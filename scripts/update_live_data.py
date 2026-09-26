import asyncio
import json
import os

from src.db_handler import DatabaseHandler
from src.park_sensor import LiveParkSensorConnector
from src.waypoint import Waypoint

CONNECTOR_ID = 677


def parse(data) -> Waypoint:
    geo_location = {"lat": data["geo_info"]["lat"], "lon": data["geo_info"]["lon"]}
    # distance with car: 117.4 ; without car: 259.5
    # fillingLevel with car: 100 ; without car: 3
    occupied = data["parsed"]["fillingLevel"] > 50
    id = str(data["device_id"])

    return Waypoint(pp_id=id, pp_belegt=occupied, pp_lat=geo_location["lat"], pp_lon=geo_location["lon"])


if __name__ == "__main__":
    while True:
        data = asyncio.run(LiveParkSensorConnector(CONNECTOR_ID, os.environ["NIOTIX_AUTH"]).get_data())
        # data = json.load(open("./example_data.json", "r"))
        waypoint = parse(data)
        DatabaseHandler().update_detection(waypoint)
        pass
