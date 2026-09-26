from src.db_handler import DatabaseHandler

from src.waypoint import Waypoint
from src.coordinates import read_municipal_csv

SOURCE_FILES = ["data/layer1.csv", "data/layer3.csv"]


def main(source_path: str):
    for lfdnr, coordinates in read_municipal_csv(source_path):
        DatabaseHandler().write_one(
            Waypoint(
                pp_id=lfdnr,
                pp_lat=coordinates.lat,
                pp_lon=coordinates.lon,
            )
        )


if __name__ == "__main__":
    for source in SOURCE_FILES:
        output = main(source)
        print(f"{source} -> {output}")
