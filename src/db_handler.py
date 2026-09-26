import csv
import sqlite3

from pydantic import BaseModel

from src.coordinates import Coordinates
from src.waypoint import Waypoint

# Layer2 is a verified byte-identical duplicate of layer1 (checked with `diff data/layer1.csv data/layer2.csv`),
# so it is deliberately skipped here to avoid double-counting spots.
PARKING_SOURCES = [
    {"attributes": "data/layer1.csv", "positions": "data/layer1_wgs84.csv"},
    {"attributes": "data/layer3.csv", "positions": "data/layer3_wgs84.csv"},
]


class ParkingSpot(BaseModel):
    id: str
    coordinates: Coordinates
    status: str | None


def _parse_time_restricted(value: str) -> bool | None:
    """Map the municipal `Z_BEGR1` column (`J`/`N`/empty) to `True`/`False`/`None`."""
    if value == "J":
        return True
    if value == "N":
        return False
    return None


def _read_attributes(path: str) -> dict[str, dict]:
    """Read a municipal attribute CSV (semicolon-separated) and index rows by `LFDNR`.

    `EIGENTUM` (owner) is only present in layer3 files; it is `None` for layer1 rows.
    """
    attributes_by_id: dict[str, dict] = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            lfdnr = row["LFDNR"]
            attributes_by_id[lfdnr] = {
                "status": row.get("STATUS") or "OCCUPIED",
            }
    return attributes_by_id


def _read_positions(path: str) -> list[tuple[str, Coordinates]]:
    """Read a `LFDNR,lat,lon` WGS84 CSV, preserving source order."""
    positions = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            positions.append((row["LFDNR"], Coordinates(lat=float(row["lat"]), lon=float(row["lon"]))))
    return positions


class DatabaseHandler:
    def __init__(self):
        self.con = sqlite3.connect("db")

    def get_all(self):
        res = self.con.execute("SELECT * FROM parkplaetze")
        res_all = res.fetchall()
        return [self._convert_db_result_to_waypoint(data) for data in res_all]

    def _convert_db_result_to_waypoint(self, data):
        return Waypoint(
            pp_id=str(data[0]),
            pp_lat=data[1],
            pp_lon=data[2],
            pp_ladesaeule_kw=data[3],
            pp_zugangsseite=data[4],
            pp_rollstuhlgerecht_level=data[5],
            pp_ueberdacht=data[6],
            pp_schranke=data[7],
            pp_bildpfad=data[8],
            pp_kostenlos=data[9],
            pp_belegt=data[10],
        )

    def update_detection(self, new_waypoint: Waypoint):
        res = self.con.execute(f"SELECT * from parkplaetze WHERE pp_id = {new_waypoint.pp_id}")
        waypoint_data = res.fetchone()
        if waypoint_data is not None:
            db_waypoint = self._convert_db_result_to_waypoint(waypoint_data)
            db_waypoint.pp_belegt = new_waypoint.pp_belegt
            self.con.execute(
                """UPDATE parkplaetze
                SET pp_lat = ?, pp_lon = ?, pp_ladesaeule_kw = ?, pp_zugangsseite = ?,
                    pp_rollstuhlgerecht_level = ?, pp_ueberdacht = ?, pp_schranke = ?,
                    pp_bildpfad = ?, pp_kostenlos = ?, pp_belegt = ?
                WHERE pp_id = ?""",
                (
                    db_waypoint.pp_lat,
                    db_waypoint.pp_lon,
                    db_waypoint.pp_ladesaeule_kw,
                    db_waypoint.pp_zugangsseite.value,
                    db_waypoint.pp_rollstuhlgerecht_level.value,
                    db_waypoint.pp_ueberdacht,
                    db_waypoint.pp_schranke,
                    db_waypoint.pp_bildpfad,
                    db_waypoint.pp_kostenlos,
                    db_waypoint.pp_belegt,
                    db_waypoint.pp_id,
                ),
            )
        else:
            self.write_one(new_waypoint)
        self.con.commit()

    def write_one(self, waypoint: Waypoint):
        self.con.execute(f"INSERT INTO parkplaetze VALUES({waypoint.get_sql_values()})")
        self.con.commit()


if __name__ == "__main__":
    # DatabaseHandler().write_one(Waypoint(pp_id="8",
    #     pp_lon=55,
    #     pp_lat=7,
    #     pp_bildpfad="developer/muensterhack_bilder",
    #     pp_ladesaeule_kw=22
    # ))
    print(DatabaseHandler().get_all())
