import asyncio
import json
from pathlib import Path

from websockets.asyncio.client import connect

from src.coordinates import Coordinates


class ParkSensor:
    def __init__(self, consumer_id: int, consumer_pass: str):
        self.consumer_id = consumer_id
        self.consumer_pass = consumer_pass
        self.geo_location: Coordinates | None = None
        self.occupied: bool | None = None

    async def get_current_detection(self):
        async with connect(f"wss://datahub.digital/api/x/websocket/consumers/{self.consumer_id}?auth={self.consumer_pass}") as websocket:
            message = await websocket.recv()
            data = json.loads(message)
            self.geo_location = Coordinates(lat=data["geo_info"]["lat"], lon=data["geo_info"]["lon"])
            # distance with car: 117.4 ; without car: 259.5
            # fillingLevel with car: 100 ; without car: 3
            self.occupied = data["parsed"]["fillingLevel"] > 50


if __name__ == "__main__":
    asyncio.run(ParkSensor(677, "ED8248EB-E8F6-4760-8B26-B8BFF9109C65").get_current_detection())
