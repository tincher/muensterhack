from dotenv import load_dotenv
from flask import Flask

from src.coordinates import Coordinates
from src.db_handler import DatabaseHandler
from src.routing import get_complete_route
from src.website_builder import WebsiteBuilder

load_dotenv()
app = Flask(__name__)


@app.route("/example_route")
def index():
    # 51.962713, 7.625652
    route = get_complete_route(Coordinates(lon=7.641, lat=51.952), Coordinates(lon=7.625652, lat=51.962713), [])
    return WebsiteBuilder().get_route_example(route).render()


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
        website_builder.add_marker()
    return website_builder.render()


@app.route("/plan")
def plan_route():
    pass
