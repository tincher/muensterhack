from pydantic import BaseModel

from src.db_handler import ParkingSpot
from src.waypoint import RollstuhlgerechtLevel, Zugangsseite


class Filter(BaseModel):
    pp_ladesaeule_kw: list[float] | None = None
    pp_zugangsseite: list[Zugangsseite] | None = None
    pp_rollstuhlgerecht_level: list[RollstuhlgerechtLevel] | None = None
    pp_ueberdacht: list[bool] | None = None
    pp_schranke: list[bool] | None = None
    pp_kostenlos: list[bool] | None = None
    pp_belegt: list[bool] | None = None

    def matches(self, spot: ParkingSpot) -> bool:
        """Check the attribute fields (owner, time_restricted, status, parking_type) against a spot.

        A `None` field never constrains. `max_wheelchair_distance_m` is not evaluated here — see
        the module docstring.
        """

        if self.pp_ladesaeule_kw is not None and spot.pp_ladesaeule_kw not in self.pp_ladesaeule_kw:
            return False
        if self.pp_zugangsseite is not None and spot.pp_zugangsseite not in self.pp_zugangsseite:
            return False
        if self.pp_rollstuhlgerecht_level is not None and spot.pp_rollstuhlgerecht_level not in self.pp_rollstuhlgerecht_level:
            return False
        if self.pp_ueberdacht is not None and spot.pp_ueberdacht not in self.pp_ueberdacht:
            return False
        if self.pp_schranke is not None and spot.pp_schranke not in self.pp_schranke:
            return False
        if self.pp_kostenlos is not None and spot.pp_kostenlos not in self.pp_kostenlos:
            return False
        if self.pp_belegt is not None and spot.pp_belegt not in self.pp_belegt:
            return False
        return True

    def apply(self, spots: list[ParkingSpot]) -> list[ParkingSpot]:
        """Return the spots that satisfy every filter in `filters` (AND semantics).

        An empty `filters` list leaves every spot eligible.
        """
        return [spot for spot in spots if self.matches(spot)]
