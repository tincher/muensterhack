import jinja2


class TemplateHandler:
    def __init__(self):
        self.env = jinja2.Environment(loader=jinja2.FileSystemLoader("./assets/maps/"))
        self.base = """var map = L.map('map').setView({lon: 7.641, lat: 51.952}, 13);
            // add the OpenStreetMap tiles
            L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
                maxZoom: 19,
                attribution: '&copy; <a href="https://openstreetmap.org/copyright">OpenStreetMap contributors</a>'
            }).addTo(map);

            // show the scale bar on the lower left corner
            L.control.scale({imperial: true, metric: true}).addTo(map);"""
        self.marker_template = "L.marker({{lon: {lon}, lat: {lat}}}).bindPopup('{popup_text}').addTo(map);"
        # self.geojson_template = r"""L.geoJSON({{data}}, {
        #                     style: function (feature) {
        #                         return {color: feature.properties.color};
        #                     }
        #                 }).bindPopup(function (layer) {
        #                     return layer.feature.properties.description;
        #                 }).addTo(map);
        #                 """
        self.geojson_template = r"""L.geoJSON({{data}}).addTo(map);
                """

    def get_example(self, template="base_map.jinja2"):
        return self.env.get_template(template).render(
            leaflet_code=self.base + self.marker_template.format(lon=7.641, lat=51.952, popup_text="Items")
        )

    def get_route_example(self, data, template="base_map.jinja2"):
        geojson_rendered = self.env.from_string(self.geojson_template).render(data=data)
        return self.env.get_template(template).render(leaflet_code=self.base + geojson_rendered)
