import os

import geojson
import requests

from src.coordinates import Coordinates


def get_route(from_: Coordinates, to_: Coordinates):
    url = "https://api.openrouteservice.org/v2/directions/wheelchair/geojson"

    headers = {
        "Authorization": os.environ["ROUTING_API_KEY"],
        "Content-type": "application/json",
    }

    data = {
        "coordinates": [[from_.lon, from_.lat], [to_.lon, to_.lat]],
        "elevation": True,
        "instructions_format": "html",
        "extra_info": ["surface", "steepness", "waytype"],
        "units": "km",
        "language": "de",
        "preference": "recommended",
        "options": {
            "profile_params": {
                "restrictions": {
                    "maximum_incline": 6,
                    "maximum_sloped_kerb": 0.06,
                    "minimum_width": 1,
                    "smoothness_type": "good",
                    "surface_type": "cobblestone",
                    "track_type": "grade1",
                },
                "surface_quality_known": False,
                "allow_unsuitable": False,
            }
        },
    }

    response = requests.post(url, headers=headers, json=data)

    return geojson.loads(response.text)


def summarize_route(route) -> dict:
    """Extracts distance, duration and the step list for the search card."""
    properties = route["features"][0]["properties"]
    summary = properties["summary"]
    return {
        "distance_km": round(summary["distance"], 1),
        "duration_min": round(summary["duration"] / 60),
        "steps": [step["instruction"] for step in properties["segments"][0]["steps"]],
    }


if __name__ == "__main__":
    print(get_route(Coordinates(lon=7.641, lat=51.952), Coordinates(lon=7.626, lat=51.962)))