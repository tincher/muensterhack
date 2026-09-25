import os

import geojson
import requests
from dotenv import load_dotenv
from geojson import Feature, FeatureCollection, LineString, Point
from pyproj import Geod

from src.coordinates import Coordinates
from src.db_handler import DatabaseHandler, ParkingSpot
from src.filter import Filter

load_dotenv()

WHEELCHAIR_URL = "https://api.openrouteservice.org/v2/directions/wheelchair/geojson"
DRIVING_CAR_URL = "https://api.openrouteservice.org/v2/directions/driving-car/geojson"
WHEELCHAIR_MATRIX_URL = "https://api.openrouteservice.org/v2/matrix/wheelchair"
DEFAULT_SHADED_URL = "https://api.shaded.openrouteservice.org/ors/v2/directions/foot-walking/geojson"
SHADE_COLUMN = "233_18"
REQUEST_TIMEOUT = 180
DEFAULT_PARKING_RADIUS_M = 300
FALLBACK_CANDIDATE_COUNT = 5

_GEOD = Geod(ellps="WGS84")

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


def _geodesic_distance_m(a: Coordinates, b: Coordinates) -> float:
    """Return the true ellipsoidal (WGS84) distance in metres between two coordinates."""
    _, _, distance = _GEOD.inv(a.lon, a.lat, b.lon, b.lat)
    return distance


def _gather_candidates(destination: Coordinates, spots: list[ParkingSpot], radius_m: float) -> list[ParkingSpot]:
    """Return the spots within `radius_m` straight-line metres of `destination`."""
    return [spot for spot in spots if _geodesic_distance_m(spot.coordinates, destination) <= radius_m]


def _narrow_to_nearest(candidates: list[ParkingSpot], destination: Coordinates, count: int = FALLBACK_CANDIDATE_COUNT) -> list[ParkingSpot]:
    """Return the `count` candidates closest to `destination` by straight-line distance, nearest first."""
    return sorted(candidates, key=lambda spot: _geodesic_distance_m(spot.coordinates, destination))[:count]


def _wheelchair_matrix_distances(candidates: list[ParkingSpot], destination: Coordinates) -> list[float | None]:
    """Return, for each candidate (same order), its wheelchair network distance to `destination` in metres.

    Uses a single ORS wheelchair matrix call. Entries are `None` where ORS could not find a route.
    """
    locations = [[spot.coordinates.lon, spot.coordinates.lat] for spot in candidates]
    locations.append([destination.lon, destination.lat])
    destination_index = len(locations) - 1
    payload = {
        "locations": locations,
        "sources": list(range(len(candidates))),
        "destinations": [destination_index],
        "metrics": ["distance"],
    }
    response = _post_ors(WHEELCHAIR_MATRIX_URL, payload)
    return [row[0] if row else None for row in response["distances"]]


def _select_by_fallback(narrowed: list[ParkingSpot], destination: Coordinates) -> ParkingSpot:
    """Fallback selection: route each of the already-narrowed candidates individually and take the shortest.

    Used when the wheelchair matrix call fails or is unavailable. `narrowed` must already be the
    same straight-line-nearest subset used for the matrix attempt, so the fallback considers exactly
    the same pool.
    """
    best_spot = None
    best_distance = None
    for spot in narrowed:
        coordinates = [[spot.coordinates.lon, spot.coordinates.lat], [destination.lon, destination.lat]]
        try:
            route = _post_ors(WHEELCHAIR_URL, _wheelchair_payload(coordinates))
        except RuntimeError:
            continue
        distance_km = route["features"][0]["properties"]["summary"]["distance"]
        distance_m = distance_km * 1000
        if best_distance is None or distance_m < best_distance:
            best_spot, best_distance = spot, distance_m
    if best_spot is None:
        raise RuntimeError("No reachable parking spot was found (fallback routing)")
    return best_spot


def select_parking_spot(
    destination: Coordinates,
    filter: Filter,
    radius_m: float = DEFAULT_PARKING_RADIUS_M,
) -> ParkingSpot:
    """Select the eligible parking spot near `destination` whose wheelchair route there is shortest.

    Candidates are gathered within `radius_m` straight-line metres of the destination, then narrowed
    by the attribute constraints of `filters` before any routing call, and then further narrowed to
    the `FALLBACK_CANDIDATE_COUNT` closest by straight-line distance (a matrix call spanning every
    in-radius candidate is unreliable — see design.md). Ranking uses a single ORS wheelchair matrix
    call over that narrowed set (network distance, not straight-line); any `max_wheelchair_distance_m`
    filter is applied as a cutoff on that matrix distance. If the matrix call fails, a bounded
    fallback routes the same narrowed candidates individually.
    """
    db_handler = DatabaseHandler()
    all_spots = db_handler.get_all_parking_spots()

    candidates = _gather_candidates(destination, all_spots, radius_m)
    if not candidates:
        raise RuntimeError(f"No parking spot is available within {radius_m} m of destination {destination}")

    eligible = filter.apply(candidates)
    if not eligible:
        raise RuntimeError(f"No parking spot satisfies the supplied filters within {radius_m} m of destination {destination}")

    narrowed = _narrow_to_nearest(eligible, destination)

    try:
        distances = _wheelchair_matrix_distances(narrowed, destination)
    except RuntimeError:
        return _select_by_fallback(narrowed, destination)

    best_spot = None
    best_distance = None
    for spot, distance_m in zip(narrowed, distances):
        if distance_m is None:
            continue
        if best_distance is None or distance_m < best_distance:
            best_spot, best_distance = spot, distance_m

    if best_spot is None:
        raise RuntimeError(f"No reachable parking spot was found near destination {destination}")
    return best_spot


def get_driving_car_route(from_: Coordinates, to_: Coordinates) -> FeatureCollection:
    coordinates = [[from_.lon, from_.lat], [to_.lon, to_.lat]]
    payload = {
        "coordinates": coordinates,
        "instructions_format": "html",
        "units": "km",
    }
    return _post_ors(DRIVING_CAR_URL, payload)


def _merge_complete_route(car_route: dict, wheelchair_route: dict, spot: ParkingSpot) -> FeatureCollection:
    """Merge a car leg and a wheelchair leg into one three-feature FeatureCollection.

    Features: car LineString (mode="driving-car"), wheelchair LineString (mode="wheelchair",
    shade_mode carrying the wheelchair leg's own route_mode), and a transfer Point at the spot.
    """
    car_feature = car_route["features"][0]
    car_properties = dict(car_feature["properties"])
    car_properties["mode"] = "driving-car"
    car_leg = Feature(geometry=LineString(car_feature["geometry"]["coordinates"]), properties=car_properties)

    wheelchair_feature = wheelchair_route["features"][0]
    wheelchair_properties = dict(wheelchair_feature["properties"])
    wheelchair_properties["mode"] = "wheelchair"
    wheelchair_properties["shade_mode"] = wheelchair_route.get("route_mode")
    wheelchair_leg = Feature(geometry=LineString(wheelchair_feature["geometry"]["coordinates"]), properties=wheelchair_properties)

    transfer_point = Feature(
        geometry=Point((spot.coordinates.lon, spot.coordinates.lat)),
        properties={
            "type": "transfer",
            "mode_from": "driving-car",
            "mode_to": "wheelchair",
            "parking_spot_id": spot.id,
        },
    )

    result = FeatureCollection([car_leg, wheelchair_leg, transfer_point])
    result["route_mode"] = "complete"
    result["parking_spot_id"] = spot.id
    return result


def get_complete_route(
    from_: Coordinates,
    to_: Coordinates,
    filter: Filter,
    radius_m: float = DEFAULT_PARKING_RADIUS_M,
) -> FeatureCollection:
    """Compute a complete car-then-wheelchair journey from `from_` to `to_`.

    Selects a disabled-parking spot near the destination (subject to `filters`), drives there by
    car, then completes the trip by wheelchair using the existing shade-optimized logic. Raises
    `RuntimeError` if no usable spot exists or if the car leg cannot be produced; never returns a
    single-mode result in place of a failed complete route.
    """
    spot = select_parking_spot(to_, filter, radius_m=radius_m)

    try:
        car_route = get_driving_car_route(from_, spot.coordinates)
    except RuntimeError as exc:
        raise RuntimeError(f"Car leg to parking spot {spot.id} could not be produced: {exc}") from exc

    wheelchair_route = get_shade_wheelchair_route(spot.coordinates, to_)

    return _merge_complete_route(car_route, wheelchair_route, spot)


if __name__ == "__main__":
    from_ = Coordinates(lon=7.641, lat=51.952)
    to_ = Coordinates(lon=7.626, lat=51.962)

    print(get_route(from_, to_))

    shaded_route = get_shade_wheelchair_route(from_, to_)
    print(shaded_route)

    complete_route = get_complete_route(from_, to_, [])
    print(complete_route)
