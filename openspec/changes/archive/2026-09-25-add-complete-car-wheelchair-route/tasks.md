# Tasks

## 1. Parking spot model and store

- [x] 1.1 Add a `ParkingSpot` pydantic model to `src/db_handler.py` with `id`, `coordinates: Coordinates`, `owner: str | None`, `time_restricted: bool | None`, `status: str | None`, `parking_type: str | None`, and verify `ParkingSpot(id="183", coordinates=Coordinates(lat=51.95, lon=7.63), owner=None, time_restricted=False, status="A", parking_type="10")` constructs without validation error
- [x] 1.2 Implement `DatabaseHandler.get_all_parking_spots() -> list[ParkingSpot]` reading positions from `data/layer1_wgs84.csv` and `data/layer3_wgs84.csv` and joining attributes by `LFDNR` from `data/layer1.csv` and `data/layer3.csv` (skip `layer2.csv`, a verified duplicate of `layer1.csv`; map `Z_BEGR1` `J`/`N`/empty to `True`/`False`/`None`, `EIGENTUM` to `owner` and `None` for layer1), and verify it returns 464 spots with 464 distinct ids, all latitudes in 51.85..52.1 and longitudes in 7.5..7.8
- [x] 1.3 De-duplicate by `LFDNR` keeping the first occurrence, and verify that appending a duplicated row to a temporary copy of a source file still yields one spot for that id

## 2. Filters

- [x] 2.1 Replace the empty `Filter` class in `src/filter.py` with a pydantic model carrying optional `owner`, `time_restricted`, `status`, `parking_type`, and `max_wheelchair_distance_m`, all defaulting to `None`, and verify `Filter()` constructs and represents "no constraint"
- [x] 2.2 Add `Filter.matches(spot: ParkingSpot) -> bool` covering only the four attribute fields (a `None` field never constrains), and verify `Filter(owner="PRI").matches(...)` is `True` for a `PRI` spot, `False` for an `NRW` spot, and `False` for a layer1 spot whose owner is `None`
- [x] 2.3 Add a helper that applies a list of filters with AND semantics and returns the eligible spots, and verify that an empty list keeps every candidate while two filters that a spot satisfies only partly exclude it
- [x] 2.4 Document in a module docstring in `src/filter.py` that `max_wheelchair_distance_m` is evaluated against the direct wheelchair network distance (not the shade-detoured leg) and is therefore applied after ranking, not in `matches`, and verify the docstring renders via `.venv/bin/python -c "import src.filter; print(src.filter.__doc__)"`

## 3. Candidate gathering and ranking in src/routing.py

- [x] 3.1 Add a geodesic distance helper using `pyproj.Geod(ellps="WGS84").inv`, and verify it returns ~719.8 m between `(lat=51.9584, lon=7.6347)` and `(lat=51.962, lon=7.626)`
- [x] 3.2 Add candidate gathering that keeps spots within a caller-adjustable radius (default 500 m) of the destination, and verify that the destination `Coordinates(lon=7.626, lat=51.962)` yields 43 candidates at 500 m and 12 at 300 m against the real data
- [x] 3.3 Apply the attribute filters to the candidates before any network call, and verify by asserting the ranking step receives only the filtered subset (e.g. with a stubbed matrix call that records the locations it was given)
- [x] 3.4 Narrow the filtered candidates to the 5 closest by straight-line distance to the destination, and verify that for the example destination this yields exactly candidates `432, 1921, 1920, 1918, 1917` in that order
- [x] 3.5 Add a wheelchair matrix request over only the narrowed 5 (`POST /v2/matrix/wheelchair`, `locations = narrowed candidates + [destination]`, `sources` the 5 candidate indices, `destinations` the last index, `metrics: ["distance"]`) reusing `_post_ors` conventions, and verify a live call for the example destination returns one distance per candidate without the HTTP 500 seen when the call spans all 43 in-radius candidates
- [x] 3.6 Drop `null` matrix entries as unroutable, apply any `max_wheelchair_distance_m` cutoff, and select the minimum-distance spot; verify with a stubbed matrix response that a `null` candidate is skipped, that an over-cutoff candidate is excluded, and that the shortest-by-route candidate wins over a closer-by-straight-line one within the narrowed 5
- [x] 3.7 Add the matrix fallback: on matrix failure, compute plain wheelchair routes for the same narrowed 5 candidates individually and take the shortest; verify by forcing the matrix call to raise `RuntimeError` and confirming a spot is still selected
- [x] 3.8 Raise `RuntimeError` with distinct messages for "no spot within radius", "no spot satisfies the filters", and "no reachable spot", and verify each by requesting a destination far outside Münster, an impossible filter, and an all-`null` stubbed matrix respectively

## 4. Car leg and result assembly

- [x] 4.1 Add a driving-car request against `https://api.openrouteservice.org/v2/directions/driving-car/geojson` via `_post_ors` with `units: "km"` and `instructions_format: "html"` and no `elevation`, and verify a live call between the example coordinates returns a `FeatureCollection` with one `LineString`
- [x] 4.2 Implement `get_complete_route(from_, to_, filters)` to select the spot, request the car leg origin→spot, request `get_shade_wheelchair_route(spot, to_)`, and verify the car leg's last coordinate and the wheelchair leg's first coordinate both sit at the selected spot (within ORS snapping tolerance)
- [x] 4.3 Merge both legs into one `FeatureCollection` of three features — car `LineString` with `properties.mode = "driving-car"`, wheelchair `LineString` with `properties.mode = "wheelchair"` and `properties.shade_mode` carrying the shade route's own `route_mode`, and a transfer `Point` at the spot with `properties = {"type": "transfer", "mode_from": "driving-car", "mode_to": "wheelchair", "parking_spot_id": ...}` — and verify all three features and their properties are present
- [x] 4.4 Set `route_mode = "complete"` and `parking_spot_id` on the returned collection, and verify both are readable on the result alongside each leg's `properties.summary.distance` and `summary.duration`
- [x] 4.5 Propagate car-leg failure as a `RuntimeError` rather than returning the wheelchair leg alone, and verify by pointing the car request at an unroutable origin that no partial route is returned

## 5. Integration verification

- [x] 5.1 Extend the `if __name__ == "__main__"` block in `src/routing.py` to call `get_complete_route` with the example coordinates and an empty filter list, and verify it prints a three-feature collection end to end
- [x] 5.2 Render the result through `WebsiteBuilder().get_route_example(route).render()` and verify the returned HTML contains both leg geometries and the transfer point, confirming no rendering change was needed
- [x] 5.3 Run `.venv/bin/ruff check src` (line-length 140 per `pyproject.toml`) and `.venv/bin/python -c "import src.routing, src.filter, src.db_handler"` and confirm no lint or import errors
