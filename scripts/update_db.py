"""Overwrite the dummy attribute values of every parking spot with random ones.

Coordinates and ids are kept as-is, `pp_kommentare` is not touched.
"""

import random

from src.db_handler import DatabaseHandler
from src.waypoint import RollstuhlgerechtLevel, Waypoint, Zugangsseite

LADESAEULE_KW_CHOICES = [0, 11, 22, 150, 300]


def randomize(waypoint: Waypoint) -> Waypoint:
    return waypoint.model_copy(
        update={
            "pp_ladesaeule_kw": random.choice(LADESAEULE_KW_CHOICES),
            "pp_zugangsseite": random.choice(list(Zugangsseite)),
            "pp_rollstuhlgerecht_level": random.choice(list(RollstuhlgerechtLevel)),
            "pp_ueberdacht": random.choice([True, False]),
            "pp_schranke": random.choice([True, False]),
            "pp_kostenlos": random.choice([True, False]),
            "pp_belegt": random.choice([True, False]),
            "pp_bildpfad": f"https://picsum.photos/seed/{waypoint.pp_id}/480/240",
        }
    )


def main():
    db = DatabaseHandler()
    waypoints = db.get_all()
    for waypoint in waypoints:
        db.update(randomize(waypoint))
    print(f"Randomized {len(waypoints)} parking spots.")


if __name__ == "__main__":
    main()
