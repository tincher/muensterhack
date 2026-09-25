from dotenv import load_dotenv
from flask import Flask, request

from src.coordinates import Coordinates
from src.geocoding import Place, geocode
from src.routing import get_route, summarize_route
from src.website_builder import WebsiteBuilder

load_dotenv()
app = Flask(__name__)


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
            route = get_route(start.coordinates, destination.coordinates)
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


@app.route("/example_marker")
def example_marker():
    return WebsiteBuilder().get_example().render()