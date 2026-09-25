import csv

from src.coordinates import read_municipal_csv

SOURCE_FILES = ["data/layer1.csv", "data/layer3.csv"]


def export_to_wgs84(source_path: str) -> str:
    """Convert a municipal CSV file to a `LFDNR,lat,lon` WGS84 CSV alongside the source, without altering it."""
    dest_path = source_path.removesuffix(".csv") + "_wgs84.csv"
    with open(dest_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["LFDNR", "lat", "lon"])
        for lfdnr, coordinates in read_municipal_csv(source_path):
            writer.writerow([lfdnr, coordinates.lat, coordinates.lon])
    return dest_path


if __name__ == "__main__":
    for source in SOURCE_FILES:
        output = export_to_wgs84(source)
        print(f"{source} -> {output}")
