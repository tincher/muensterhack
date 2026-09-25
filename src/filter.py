"""Parking-spot eligibility filters.

A `Filter` constrains which parking spots are eligible for selection. Its `owner`,
`time_restricted`, `status`, and `parking_type` fields are matched against a spot's attributes via
`Filter.matches`, and can be checked before any routing call is made.

`max_wheelchair_distance_m` is different: it must be evaluated against the *direct* wheelchair
network distance from a spot to the destination (the distance an ORS matrix call reports), not
against the shade-detoured wheelchair leg that is actually travelled. That direct distance is only
known once candidates have been ranked, so `max_wheelchair_distance_m` is deliberately not checked
in `matches` — it is applied as a cutoff after ranking, in the candidate-selection logic in
`src/routing.py`.
"""

from pydantic import BaseModel

from src.db_handler import ParkingSpot


class Filter(BaseModel):
    owner: str | None = None
    time_restricted: bool | None = None
    status: str | None = None
    parking_type: str | None = None
    max_wheelchair_distance_m: float | None = None

    def matches(self, spot: ParkingSpot) -> bool:
        """Check the attribute fields (owner, time_restricted, status, parking_type) against a spot.

        A `None` field never constrains. `max_wheelchair_distance_m` is not evaluated here — see
        the module docstring.
        """
        if self.owner is not None and spot.owner != self.owner:
            return False
        if self.time_restricted is not None and spot.time_restricted != self.time_restricted:
            return False
        if self.status is not None and spot.status != self.status:
            return False
        return not (self.parking_type is not None and spot.parking_type != self.parking_type)


def apply_filters(filters: list[Filter], spots: list[ParkingSpot]) -> list[ParkingSpot]:
    """Return the spots that satisfy every filter in `filters` (AND semantics).

    An empty `filters` list leaves every spot eligible.
    """
    return [spot for spot in spots if all(f.matches(spot) for f in filters)]
