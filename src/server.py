import sqlite3

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from pyproj import Geod

from src.coordinates import Coordinates
from src.db_handler import DatabaseHandler
from src.filter import Filter
from src.geocoding import Place, geocode
from src.routing import get_complete_route, get_route, summarize_route
from src.waypoint import Waypoint
from src.website_builder import WebsiteBuilder

load_dotenv()
app = Flask(__name__, static_folder="../assets", static_url_path="/assets")

# Parking spot at the destination ("P" icon): the nearest one within this radius
PARKING_RADIUS_M = 300
PARKING_COUNT = 1
# After a route search, the other parking spots (blue pins) are only shown within this radius
# around the destination, so the map is not overloaded. Change the number to show more or fewer.
OTHER_PARKING_RADIUS_M = 500

_GEOD = Geod(ellps="WGS84")


def parse_coordinates(text: str) -> Coordinates | None:
    """Reads 'lat,lon' as sent by the 'my location' button. Returns None if invalid."""
    try:
        lat, lon = (float(part) for part in text.split(","))
    except ValueError:
        return None
    if -90 <= lat <= 90 and -180 <= lon <= 180:
        return Coordinates(lat=lat, lon=lon)
    return None


def load_waypoints() -> list[Waypoint]:
    """All parking spots from the database (empty list if the database is not available)."""
    try:
        return DatabaseHandler().get_all()
    except sqlite3.Error:
        return []


def parking_within(center: Coordinates, waypoints: list[Waypoint], radius_m: float) -> list[tuple[Waypoint, float]]:
    """All parking spots within radius_m of center, with their distance in metres, nearest first."""
    nearby = []
    for waypoint in waypoints:
        _, _, distance_m = _GEOD.inv(waypoint.pp_lon, waypoint.pp_lat, center.lon, center.lat)
        if distance_m <= radius_m:
            nearby.append((waypoint, distance_m))
    nearby.sort(key=lambda item: item[1])
    return nearby


def parking_near(destination: Coordinates, waypoints: list[Waypoint]) -> list[tuple[Waypoint, float]]:
    """The PARKING_COUNT nearest parking spots within PARKING_RADIUS_M of the destination."""
    return parking_within(destination, waypoints, PARKING_RADIUS_M)[:PARKING_COUNT]


@app.route("/")
def index():
    start_text = request.args.get("start", "").strip()
    start_coords = request.args.get("start_coords", "").strip()
    destination_text = request.args.get("destination", "").strip()

    builder = WebsiteBuilder()
    error = None
    route_info = None
    waypoints = load_waypoints()
    shown_waypoints = waypoints  # without a route: all parking spots
    destination_parking_ids: set[str] = set()

    if start_text and destination_text:
        # "My location" sends exact coordinates, otherwise the typed address is looked up
        my_location = parse_coordinates(start_coords) if start_coords else None
        start = Place(coordinates=my_location, label="Mein Standort") if my_location else geocode(start_text)
        destination = geocode(destination_text)

        hint = "Bitte Schreibweise prüfen oder Straße mit Hausnummer eingeben."
        if start is None:
            error = f"Der Start „{start_text}“ wurde in Münster nicht gefunden. {hint}"
        elif destination is None:
            error = f"Das Ziel „{destination_text}“ wurde in Münster nicht gefunden. {hint}"
        else:
            try:
                route = get_route([start.coordinates, destination.coordinates])
            except RuntimeError:
                route = {}
            if route.get("features"):
                builder.add_route(route)
                route_info = summarize_route(route)

                # Parking at the destination: gets the "P" icon
                nearby = parking_near(destination.coordinates, waypoints)
                destination_parking_ids = {waypoint.pp_id for waypoint, _ in nearby}

                # Other parking spots: only those close to the destination (blue pins)
                shown_waypoints = [
                    waypoint
                    for waypoint, _ in parking_within(destination.coordinates, waypoints, OTHER_PARKING_RADIUS_M)
                ]

                route_info["parking"] = [
                    {"name": waypoint.pp_id, "distance_m": round(distance_m)} for waypoint, distance_m in nearby
                ]
            else:
                error = "Für diese Strecke wurde keine barrierefreie Route gefunden."

    for waypoint in shown_waypoints:
        builder.add_waypoint(waypoint, highlight=waypoint.pp_id in destination_parking_ids)

    return builder.render(
        start=start_text,
        start_coords=start_coords,
        destination=destination_text,
        route_info=route_info,
        parking_radius_m=PARKING_RADIUS_M,
        error=error,
    )


@app.route("/route", methods=["POST"])
def route():
    payload = request.get_json()
    points = [Coordinates(**point) for point in payload["points"]]
    return jsonify(get_route(points))


@app.route("/example_route")
def example_route():
    route = get_complete_route(from_=Coordinates(lon=7.625652, lat=51.962713), to_=Coordinates(lon=7.641, lat=51.952), filter=Filter())
    return WebsiteBuilder().get_route_example(route).render()


@app.route("/example_marker")
def example_marker():
    return WebsiteBuilder().get_example().render()


@app.route("/map")
@app.route("/example_waypoints")
def parking_map():
    """All parking spots, without a route."""
    builder = WebsiteBuilder()
    for waypoint in load_waypoints():
        builder.add_waypoint(waypoint)
    return builder.render()