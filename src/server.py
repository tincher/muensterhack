from dotenv import load_dotenv
from flask import Flask

from src.coordinates import Coordinates
from src.routing import get_shade_wheelchair_route
from src.website_builder import WebsiteBuilder

load_dotenv()
app = Flask(__name__)


@app.route("/")
def index():
    route = get_shade_wheelchair_route(Coordinates(lon=7.641, lat=51.952), Coordinates(lon=7.626, lat=51.962))
    return WebsiteBuilder().get_route_example(route).render()


@app.route("/example_marker")
def example_marker():
    return WebsiteBuilder().get_example().render()
