import os

import geojson
import requests
from dotenv import load_dotenv
from geojson import FeatureCollection

from src.coordinates import Coordinates

load_dotenv()

WHEELCHAIR_URL = "https://api.openrouteservice.org/v2/directions/wheelchair/geojson"
DEFAULT_SHADED_URL = "https://api.shaded.openrouteservice.org/ors/v2/directions/foot-walking/geojson"
SHADE_COLUMN = "233_18"
REQUEST_TIMEOUT = 180

WHEELCHAIR_RESTRICTIONS = {
    "maximum_incline": 6,
    "maximum_sloped_kerb": 0.06,
    "minimum_width": 1,
    "smoothness_type": "good",
    "surface_type": "cobblestone",
    "track_type": "grade1",
}

WHEELCHAIR_PROFILE_PARAMS = {
    "restrictions": WHEELCHAIR_RESTRICTIONS,
    "surface_quality_known": False,
    "allow_unsuitable": False,
}


def _shaded_api_key():
    return os.environ["ROUTING_API_KEY"]


def _headers(api_key: str) -> dict[str, str]:
    return {"Authorization": api_key, "Content-type": "application/json"}


def _post_ors(url: str, payload: dict, api_key: str | None = None) -> dict:
    response = requests.post(url, headers=_headers(api_key or os.environ["ROUTING_API_KEY"]), json=payload, timeout=REQUEST_TIMEOUT)
    if response.status_code != 200:
        raise RuntimeError(f"ORS request to {url} returned HTTP {response.status_code}: {response.text}")
    return geojson.loads(response.text)


def _wheelchair_payload(coordinates, instructions_format: str = "text", extra_info: list[str] | None = None) -> dict:
    payload = {
        "coordinates": coordinates,
        "elevation": True,
        "instructions_format": instructions_format,
        "language": "en",
        "units": "km",
        "preference": "recommended",
        "options": {"profile_params": WHEELCHAIR_PROFILE_PARAMS},
    }
    if extra_info:
        payload["extra_info"] = extra_info
    return payload


def _sample_waypoints(coordinates, num_waypoints: int = 20):
    step = max(1, len(coordinates) // num_waypoints)
    waypoints = [point[:2] for point in coordinates[::step]]
    if waypoints[-1] != coordinates[-1][:2]:
        waypoints.append(coordinates[-1][:2])
    return waypoints


def get_route(from_: Coordinates, to_: Coordinates) -> dict:
    coordinates = [[from_.lon, from_.lat], [to_.lon, to_.lat]]
    payload = _wheelchair_payload(coordinates, instructions_format="html", extra_info=["surface", "steepness", "waytype"])
    return _post_ors(WHEELCHAIR_URL, payload)


def get_shade_wheelchair_route(
    from_: Coordinates, to_: Coordinates, num_waypoints: int = 12, shade_factor: float = -1
) -> FeatureCollection:
    coordinates = [[from_.lon, from_.lat], [to_.lon, to_.lat]]
    shade_payload = {
        "coordinates": coordinates,
        "elevation": True,
        "instructions_format": "text",
        "language": "en",
        "units": "km",
        "preference": "recommended",
        "options": {
            "profile_params": {"weightings": {"csv_factor": shade_factor, "csv_column": SHADE_COLUMN}},
            "avoid_features": ["ferries"],
        },
    }

    shade_route = _post_ors(DEFAULT_SHADED_URL, shade_payload, api_key=_shaded_api_key())
    waypoints = _sample_waypoints(shade_route["features"][0]["geometry"]["coordinates"], num_waypoints)

    try:
        route = _post_ors(WHEELCHAIR_URL, _wheelchair_payload(waypoints))
        route["route_mode"] = "combined"
    except RuntimeError:
        route = _post_ors(WHEELCHAIR_URL, _wheelchair_payload(coordinates))
        route["route_mode"] = "fallback"
    return route


if __name__ == "__main__":
    from_ = Coordinates(lon=7.641, lat=51.952)
    to_ = Coordinates(lon=7.626, lat=51.962)

    print(get_route(from_, to_))

    shaded_route = get_shade_wheelchair_route(from_, to_)
    print(shaded_route)
