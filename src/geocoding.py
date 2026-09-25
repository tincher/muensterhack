import os

import requests
from pydantic import BaseModel

from src.coordinates import Coordinates

GEOCODE_URL = "https://api.openrouteservice.org/geocode/{endpoint}"

# Center of Münster: results near the city centre are ranked first
MUENSTER = Coordinates(lon=7.626, lat=51.962)

# Rectangle around the city of Münster: only places inside it are returned,
# so "Hauptbahnhof" can never end up at a station in another town
MUENSTER_AREA = {
    "boundary.rect.min_lon": 7.47,
    "boundary.rect.min_lat": 51.84,
    "boundary.rect.max_lon": 7.78,
    "boundary.rect.max_lat": 52.06,
}


class Place(BaseModel):
    coordinates: Coordinates
    label: str


def _query(endpoint: str, text: str, size: int = 1) -> list[Place]:
    """Asks one openrouteservice geocoding endpoint ('search' or 'autocomplete')."""
    params = {
        "api_key": os.environ["ROUTING_API_KEY"],
        "text": text,
        "focus.point.lon": MUENSTER.lon,
        "focus.point.lat": MUENSTER.lat,
        **MUENSTER_AREA,
    }
    if endpoint == "search":
        params["size"] = size

    response = requests.get(GEOCODE_URL.format(endpoint=endpoint), params=params, timeout=10)
    response.raise_for_status()

    places = []
    for feature in response.json().get("features", []):
        lon, lat = feature["geometry"]["coordinates"][:2]
        label = feature.get("properties", {}).get("label") or text
        places.append(Place(coordinates=Coordinates(lon=lon, lat=lat), label=label))
    return places


def geocode(text: str) -> Place | None:
    """Finds the best matching place in Münster for an address or place name.

    The normal search is tried first, the more forgiving autocomplete second
    (it also finds unfinished names).
    """
    for endpoint in ("search", "autocomplete"):
        places = _query(endpoint, text)
        if places:
            return places[0]
    return None