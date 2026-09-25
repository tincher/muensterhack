from dotenv import load_dotenv
from flask import Flask, jsonify, request

from src.coordinates import Coordinates
from src.db_handler import DatabaseHandler
from src.filter import Filter
from src.routing import get_complete_route, get_route
from src.test_data import get_test_waypoints
from src.website_builder import WebsiteBuilder

load_dotenv()
app = Flask(__name__, static_folder="../assets", static_url_path="/assets")


@app.route("/example_route")
def index():
    # 51.962713, 7.625652
    route = get_complete_route(from_=Coordinates(lon=7.625652, lat=51.962713), to_=Coordinates(lon=7.641, lat=51.952), filter=Filter())
    return WebsiteBuilder().get_route_example(route).render()


@app.route("/route", methods=["POST"])
def route():
    payload = request.get_json()
    points = [Coordinates(**point) for point in payload["points"]]
    return jsonify(get_route(points))


@app.route("/example_marker")
def example_marker():
    return WebsiteBuilder().get_example().render()


@app.route("/")
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
