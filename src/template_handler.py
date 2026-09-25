import jinja2


class TemplateHandler:
    def __init__(self):
        self.env = jinja2.Environment(loader=jinja2.FileSystemLoader("./assets/maps/"))
        self.marker_template = "L.marker({{lon: {lon}, lat: {lat}}}).bindPopup('{popup_text}').addTo(map);"

    def get_example(self, template="base_map.jinja2"):
        return self.env.get_template(template).render(markers_js=self.marker_template.format(lon=7.641, lat=51.952, popup_text="Items"))
