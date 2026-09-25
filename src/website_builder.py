import jinja2

from src.waypoint import Waypoint


class WebsiteConfig:
    code: str = """var map = L.map('map').setView({lon: 7.641, lat: 51.952}, 13);
            // add the OpenStreetMap tiles
            var osm = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
                maxZoom: 19,
                attribution: '&copy; <a href="https://openstreetmap.org/copyright">OpenStreetMap contributors</a>'
            }).addTo(map);

            // Alternative 1: Stadia Outdoors
            var stadiaOutdoors = L.tileLayer('https://tiles.stadiamaps.com/tiles/outdoors/{z}/{x}/{y}{r}.{ext}', {
                minZoom: 0,
                maxZoom: 20,
                attribution: '&copy; <a href="https://www.stadiamaps.com/" target="_blank">Stadia Maps</a> &copy; <a href="https://openmaptiles.org/" target="_blank">OpenMapTiles</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
                ext: 'png'
            });

            // Alternative 2: Satellitenbild (Esri)
            var satellit = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
                maxZoom: 19,
                attribution: 'Tiles &copy; Esri &mdash; Source: Esri, Vantor, Earthstar Geographics, and the GIS User Community'
            });

            // Design der Kartenauswahl (gleiche Farben und Schrift wie die Suchkarte)
            var stil = document.createElement('style');
            stil.textContent = `
                .karten-auswahl {
                    display: flex;
                    gap: 4px;
                    padding: 5px;
                    background: #fff;
                    border-radius: 999px;
                    box-shadow: 0 4px 20px rgba(19, 41, 51, 0.18);
                    font-family: 'Atkinson Hyperlegible', system-ui, sans-serif;
                }
                .karten-knopf {
                    min-height: 40px;
                    padding: 0 16px;
                    border: none;
                    border-radius: 999px;
                    background: transparent;
                    font: inherit;
                    font-size: 15px;
                    font-weight: 700;
                    color: #132933;
                    cursor: pointer;
                    transition: background 0.15s, color 0.15s;
                }
                .karten-knopf:hover { background: #e0f2dc; }
                .karten-knopf[aria-pressed="true"] { background: #2b5d79; color: #fff; }
                .karten-knopf:focus-visible {
                    outline: 3px solid #e6af44;
                    outline-offset: 2px;
                    box-shadow: 0 0 0 5px #132933;
                }
                @media (prefers-reduced-motion: reduce) {
                    .karten-knopf { transition: none; }
                }
            `;
            document.head.appendChild(stil);

            // Kartenauswahl als Knopfleiste (oben rechts)
            var karten = [
                {name: 'Stadtplan', layer: osm},
                {name: 'Natur', layer: stadiaOutdoors},
                {name: 'Satellit', layer: satellit}
            ];
            var aktiveKarte = osm;

            var KartenAuswahl = L.Control.extend({
                options: {position: 'topright'},
                onAdd: function () {
                    var box = L.DomUtil.create('div', 'karten-auswahl');
                    box.setAttribute('role', 'group');
                    box.setAttribute('aria-label', 'Kartenstil wählen');
                    L.DomEvent.disableClickPropagation(box);

                    karten.forEach(function (k) {
                        var knopf = L.DomUtil.create('button', 'karten-knopf', box);
                        knopf.type = 'button';
                        knopf.textContent = k.name;
                        knopf.setAttribute('aria-pressed', k.layer === aktiveKarte ? 'true' : 'false');

                        knopf.addEventListener('click', function () {
                            map.removeLayer(aktiveKarte);
                            k.layer.addTo(map);
                            aktiveKarte = k.layer;
                            box.querySelectorAll('.karten-knopf').forEach(function (b) {
                                b.setAttribute('aria-pressed', 'false');
                            });
                            knopf.setAttribute('aria-pressed', 'true');
                        });
                    });
                    return box;
                }
            });
            new KartenAuswahl().addTo(map);

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
        self.geojson_template = r"""var route = L.geoJSON({{data}}, {style: {color: '#2b5d79', weight: 6, opacity: 0.9} }).addTo(map);
        map.fitBounds(route.getBounds(), {padding: [40, 40]});"""
        self.website_config = WebsiteConfig()

    def render(self, **template_vars):
        return self.env.get_template("base_map.jinja2").render(
            leaflet_code=self.website_config.code, **template_vars
        )

    def add_marker(self, lat: float, lon: float, popup_text: str):
        self.website_config.append(self.marker_template.format(lon=lon, lat=lat, popup_text=popup_text))
        return self

    def add_waypoint(self, waypoint: Waypoint):
        self.website_config.append(
            self.waypoint_marker_template.format(lon=waypoint.pp_lon, lat=waypoint.pp_lat, data=waypoint.model_dump_json())
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