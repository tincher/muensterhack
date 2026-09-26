from dotenv import load_dotenv
from flask import Flask, jsonify, request

from src.coordinates import Coordinates
from src.db_handler import DatabaseHandler
from src.filter import Filter
from src.routing import get_complete_route, get_route, summarize_route
from src.website_builder import WebsiteBuilder
from src.geocoding import Place,geocode

load_dotenv()
app = Flask(__name__, static_folder="../assets", static_url_path="/assets")


@app.route("/example_route")
def example_route():
    # 51.962713, 7.625652
    route = get_complete_route(from_=Coordinates(lon=7.625652, lat=51.962713), to_=Coordinates(lon=7.641, lat=51.952), filter=Filter())
    return WebsiteBuilder().get_route_example(route).render()
def parse_coordinates(text: str) -> Coordinates | None:
    """Reads 'lat,lon' as sent by the 'my location' button. Returns None if invalid."""
    try:
        lat, lon = (float(part) for part in text.split(","))
    except ValueError:
        return None
    if -90 <= lat <= 90 and -180 <= lon <= 180:
        return Coordinates(lat=lat, lon=lon)
    return None


@app.route("/")
def index():
    start_text = request.args.get("start", "").strip()
    start_coords = request.args.get("start_coords", "").strip()
    destination_text = request.args.get("destination", "").strip()

    builder = WebsiteBuilder()
    error = None
    route_info = None

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
            route = get_route([start.coordinates, destination.coordinates])
            if route.get("features"):
                builder.add_route(route)
                route_info = summarize_route(route)
                # Show which places were actually used, so wrong matches are easy to spot
                route_info["from_label"] = start.label
                route_info["to_label"] = destination.label
            else:
                error = "Für diese Strecke wurde keine barrierefreie Route gefunden."

    return builder.render(
        start=start_text,
        start_coords=start_coords,
        destination=destination_text,
        route_info=route_info,
        error=error,
    )


@app.route("/route", methods=["POST"])
def route():
    payload = request.get_json()
    points = [Coordinates(**point) for point in payload["points"]]
    return jsonify(get_route(points))


@app.route("/example_marker")
def example_marker():
    return WebsiteBuilder().get_example().render()


@app.route("/map")
def map():
    website_builder = WebsiteBuilder()
    db_handler = DatabaseHandler()
    parking_spots = db_handler.get_all_parking_spots()
    for parking_spot in parking_spots:
        website_builder.add_marker(lat=parking_spot.coordinates.lat, lon=parking_spot.coordinates.lon, popup_text=parking_spot.status)
    return website_builder.render()


@app.route("/plan")
def plan_route():
    pass


@app.route("/example_waypoints")
def example_waypoints():
    builder = WebsiteBuilder()
    parking_spots = DatabaseHandler().get_all()
    for parking_spot in parking_spots:
        builder.add_waypoint(parking_spot)
    return builder.render()
