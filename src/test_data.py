"""Temporary sample data for manually testing the waypoint panel. Delete once real data exists."""

from src.waypoint import Barrierefreiheitslevel, Waypoint, Zugangsseite


def get_test_waypoints() -> list[Waypoint]:
    return [
        Waypoint(
            pp_id="Parkplatz Domplatz",
            pp_lat=51.9625,
            pp_lon=7.6268,
            pp_bildpfad="https://picsum.photos/seed/domplatz/480/240",
            pp_ladesaeule_kw=22,
            pp_zugangsseite=Zugangsseite.RECHTS,
            pp_barrierefreiheit_level=Barrierefreiheitslevel.VOLL,
            pp_ueberdacht=True,
            pp_schranke=False,
            pp_kostenlos=False,
            pp_belegt=False,
            pp_kommentare=["Gut ausgeleuchtet", "Nahe am Aufzug"],
        ),
        Waypoint(
            pp_id="Parkplatz Aasee",
            pp_lat=51.9505,
            pp_lon=7.6135,
            pp_bildpfad=None,
            pp_ladesaeule_kw=None,
            pp_zugangsseite=Zugangsseite.UNBEKANNT,
            pp_barrierefreiheit_level=Barrierefreiheitslevel.UNBEKANNT,
            pp_ueberdacht=False,
            pp_schranke=False,
            pp_kostenlos=True,
            pp_belegt=None,
            pp_kommentare=[],
        ),
        Waypoint(
            pp_id="Parkplatz Hauptbahnhof",
            pp_lat=51.9489,
            pp_lon=7.6413,
            pp_bildpfad="https://picsum.photos/seed/hbf/480/240",
            pp_ladesaeule_kw=None,
            pp_zugangsseite=Zugangsseite.LINKS,
            pp_barrierefreiheit_level=Barrierefreiheitslevel.NICHT,
            pp_ueberdacht=True,
            pp_schranke=True,
            pp_kostenlos=False,
            pp_belegt=True,
            pp_kommentare=["Schranke erfordert Parkticket", "Enger Einstieg"],
        ),
        Waypoint(
            pp_id="Parkplatz Schlossgarten",
            pp_lat=51.9598,
            pp_lon=7.5975,
            pp_bildpfad="https://picsum.photos/seed/schlossgarten/480/240",
            pp_ladesaeule_kw=150,
            pp_zugangsseite=Zugangsseite.BEIDSEITIG,
            pp_barrierefreiheit_level=Barrierefreiheitslevel.TEILWEISE,
            pp_ueberdacht=False,
            pp_schranke=False,
            pp_kostenlos=False,
            pp_belegt=False,
            pp_kommentare=["Kies-Untergrund im hinteren Bereich"],
        ),
    ]
