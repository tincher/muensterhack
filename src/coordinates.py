import csv
from collections.abc import Iterator

from pydantic import BaseModel
from pyproj import Transformer

# The project's municipal CSV data (data/layer*.csv) stores positions as easting/northing in
# ETRS89 / UTM zone 32N (EPSG:25832), Germany's standard cadastral grid. `always_xy=True` forces
# both CRSs to use (x, y) axis order — i.e. (easting, northing) in, (lon, lat) out — instead of
# each CRS's own declared order (EPSG:4326 is natively (lat, lon)). Without it, the output axes
# would be silently swapped.
_UTM32_TO_WGS84 = Transformer.from_crs("EPSG:25832", "EPSG:4326", always_xy=True)


class Coordinates(BaseModel):
    lat: float
    lon: float


def utm32_to_wgs84(easting: float, northing: float) -> Coordinates:
    """Convert an ETRS89 / UTM zone 32N (EPSG:25832) easting/northing pair to WGS84 (EPSG:4326) lat/lon."""
    lon, lat = _UTM32_TO_WGS84.transform(easting, northing)
    return Coordinates(lat=lat, lon=lon)


def _parse_decimal_comma(value: str) -> float:
    """Parse a number using a comma decimal mark (e.g. "406184,039" -> 406184.039)."""
    return float(value.replace(",", "."))


def read_municipal_csv(path: str) -> Iterator[tuple[str, Coordinates]]:
    """Read a municipal CSV file (semicolon-separated, comma decimal mark) and yield (LFDNR, Coordinates).

    Position columns are located by header name (`RECHTSWERT`/`HOCHWERT`) rather than index, since
    files differ in which other columns they carry (e.g. `layer3.csv` has an extra `EIGENTUM` column).
    """
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            lfdnr = row["LFDNR"]
            try:
                easting = _parse_decimal_comma(row["RECHTSWERT"])
                northing = _parse_decimal_comma(row["HOCHWERT"])
            except (KeyError, ValueError) as exc:
                raise ValueError(f"Row with LFDNR {lfdnr!r} has an invalid position value: {exc}") from exc
            yield lfdnr, utm32_to_wgs84(easting, northing)
