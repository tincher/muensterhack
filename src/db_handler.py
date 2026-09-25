import csv
import sqlite3

from pydantic import BaseModel

from src.coordinates import Coordinates

# Layer2 is a verified byte-identical duplicate of layer1 (checked with `diff data/layer1.csv data/layer2.csv`),
# so it is deliberately skipped here to avoid double-counting spots.
PARKING_SOURCES = [
    {"attributes": "data/layer1.csv", "positions": "data/layer1_wgs84.csv"},
    {"attributes": "data/layer3.csv", "positions": "data/layer3_wgs84.csv"},
]


class ParkingSpot(BaseModel):
    id: str
    coordinates: Coordinates
    owner: str | None
    time_restricted: bool | None
    status: str | None
    parking_type: str | None


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
                "owner": row.get("EIGENTUM") or None,
                "time_restricted": _parse_time_restricted(row.get("Z_BEGR1", "")),
                "status": row.get("STATUS") or None,
                "parking_type": row.get("BEH_ART") or None,
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
        self.con = sqlite3.connect("parking.db")

    def get_current_occupation(self):
        pass

    def write_occupation(self, id, occupation):
        pass

    def get_all_parking_spots(self) -> list[ParkingSpot]:
        """Return all known disabled-parking spots, de-duplicated by `LFDNR`.

        Positions come from the already-exported `data/layer*_wgs84.csv` files; attributes come
        from the corresponding original municipal CSVs, joined by `LFDNR`. `data/layer2.csv` is a
        verified duplicate of `data/layer1.csv` and is not read. If a `LFDNR` were ever recorded in
        more than one source, only its first occurrence is kept.
        """
        spots: list[ParkingSpot] = []
        seen_ids: set[str] = set()
        for source in PARKING_SOURCES:
            attributes_by_id = _read_attributes(source["attributes"])
            for lfdnr, coordinates in _read_positions(source["positions"]):
                if lfdnr in seen_ids:
                    continue
                seen_ids.add(lfdnr)
                attributes = attributes_by_id.get(lfdnr, {})
                spots.append(
                    ParkingSpot(
                        id=lfdnr,
                        coordinates=coordinates,
                        owner=attributes.get("owner"),
                        time_restricted=attributes.get("time_restricted"),
                        status=attributes.get("status"),
                        parking_type=attributes.get("parking_type"),
                    )
                )
        return spots


if __name__ == "__main__":
    DatabaseHandler().get_current_occupation()
