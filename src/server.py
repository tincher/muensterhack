from dotenv import load_dotenv
from flask import Flask, jsonify, request

from src.coordinates import Coordinates
from src.routing import get_route
from src.test_data import get_test_waypoints
from src.website_builder import WebsiteBuilder

load_dotenv()
app = Flask(__name__, static_folder="../assets", static_url_path="/assets")


@app.route("/")
def index():
    route = get_route([Coordinates(lon=7.641, lat=51.952), Coordinates(lon=7.626, lat=51.962)])
    return WebsiteBuilder().get_route_example(route).render()


@app.route("/route", methods=["POST"])
def route():
    payload = request.get_json()
    points = [Coordinates(**point) for point in payload["points"]]
    return jsonify(get_route(points))


@app.route("/example_marker")
def example_marker():
    return WebsiteBuilder().get_example().render()


@app.route("/example_waypoints")
def example_waypoints():
    builder = WebsiteBuilder()
    for waypoint in get_test_waypoints():
        builder.add_waypoint(waypoint)
    return builder.render()
