from dotenv import load_dotenv
from flask import Flask

from src.coordinates import Coordinates
from src.routing import get_route
from src.template_handler import TemplateHandler

load_dotenv()
app = Flask(__name__)
template_handler = TemplateHandler()


@app.route("/")
def index():
    route = get_route(Coordinates(lon=7.641, lat=51.952), Coordinates(lon=7.626, lat=51.962))
    return template_handler.get_route_example(route)


@app.route("/example_marker")
def example_marker():
    return template_handler.get_example()
