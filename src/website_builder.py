import jinja2

from src.waypoint import Waypoint


class WebsiteConfig:
    code: str = """var map = L.map('map').setView({lon: 7.641, lat: 51.952}, 13);
            // add the OpenStreetMap tiles
            L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
                maxZoom: 19,
                attribution: '&copy; <a href="https://openstreetmap.org/copyright">OpenStreetMap contributors</a>'
            }).addTo(map);

            // show the scale bar on the lower left corner
            L.control.scale({imperial: true, metric: true}).addTo(map);"""

    def append(self, new_code):
        self.code = self.code + new_code


class WebsiteBuilder:
    def __init__(self):
        self.env = jinja2.Environment(loader=jinja2.FileSystemLoader("./assets/maps/"))
        self.marker_template = "L.marker({{lon: {lon}, lat: {lat}}}).bindPopup('{popup_text}').addTo(map);"
        self.waypoint_marker_template = "registerWaypointMarker({lon}, {lat}, {data});"
        # self.geojson_template = r"""L.geoJSON({{data}}, {
        #                     style: function (feature) {
        #                         return {color: feature.properties.color};
        #                     }
        #                 }).bindPopup(function (layer) {
        #                     return layer.feature.properties.description;
        #                 }).addTo(map);
        #                 """
        self.geojson_template = r"""L.geoJSON({{data}}).addTo(map);"""
        self.website_config = WebsiteConfig()

    def render(self):
        return self.env.get_template("base_map.jinja2").render(leaflet_code=self.website_config.code)

    def add_marker(self, lat: float, lon: float, popup_text: str):
        self.website_config.append(self.marker_template.format(lon=lon, lat=lat, popup_text=popup_text))
        return self

    def add_waypoint(self, waypoint: Waypoint):
        self.website_config.append(
            self.waypoint_marker_template.format(
                lon=waypoint.pp_lon, lat=waypoint.pp_lat, data=waypoint.model_dump_json()
            )
        )
        return self

    def add_route(self, data):
        self.website_config.append(self.env.from_string(self.geojson_template).render(data=data))
        return self

    def get_example(self):
        self.add_marker(lon=7.641, lat=51.952, popup_text="Items")
        return self

    def get_route_example(self, data):
        self.add_route(data)
        return self

    # def get_example(self, template="base_map.jinja2"):
    #     return self.env.get_template(template).render(
    #         leaflet_code=self.base + self.marker_template.format(lon=7.641, lat=51.952, popup_text="Items")
    #     )

    # def get_route_example(self, data, template="base_map.jinja2"):
    #     geojson_rendered = self.env.from_string(self.geojson_template).render(data=data)
    #     return self.env.get_template(template).render(leaflet_code=self.base + geojson_rendered)
