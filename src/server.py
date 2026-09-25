from flask import Flask
import jinja2


app = Flask(__name__)
env = jinja2.Environment(loader=jinja2.FileSystemLoader("./assets/maps/"))


marker_template = (
    "L.marker({{lon: {lon}, lat: {lat}}}).bindPopup('{popup_text}').addTo(map);"
)


@app.route("/")
def index():
    print(marker_template.format(lon=7.641, lat=51.952, popup_text="items"))
    return env.get_template("base_map.jinja2").render(
        markers_js=marker_template.format(lon=7.641, lat=51.952, popup_text="items")
    )
