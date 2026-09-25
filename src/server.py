from flask import Flask
import jinja2


app = Flask(__name__)
env = jinja2.Environment(loader=jinja2.FileSystemLoader("./assets/maps/"))


@app.route("/")
def index():
    return env.get_template("base_map.jinja2").render(
        marker_lon=7.641, marker_lat=51.952
    )
