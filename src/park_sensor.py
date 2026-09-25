import asyncio
import json
import os

from pydantic import BaseModel
from websockets.asyncio.client import connect

from src.coordinates import Coordinates

SENSOR_ID = 677


class ParkSensor(BaseModel):
    id: str
    geo_location: Coordinates
    occupied: bool


class ParkSensorConnector:
    def __init__(self, consumer_id: int, consumer_pass: str):
        self.consumer_id = consumer_id
        self.consumer_pass = consumer_pass

    async def get_data(self):
        async with connect(f"wss://datahub.digital/api/x/websocket/consumers/{self.consumer_id}?auth={self.consumer_pass}") as websocket:
            message = await websocket.recv()
            data = json.loads(message)
            self.geo_location = Coordinates(lat=data["geo_info"]["lat"], lon=data["geo_info"]["lon"])
            # distance with car: 117.4 ; without car: 259.5
            # fillingLevel with car: 100 ; without car: 3
            self.occupied = data["parsed"]["fillingLevel"] > 50


if __name__ == "__main__":
    asyncio.run(ParkSensor(SENSOR_ID, os.environ["NIOTIX_AUTH"]).get_current_detection())
