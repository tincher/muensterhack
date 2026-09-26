# Proposal

## Why

A wheelchair user travelling across Münster rarely rolls the whole way: they drive (or are driven) to a disabled-parking spot near the destination and cover the last stretch in the wheelchair. The codebase only routes a single mode end to end, so this real trip cannot be planned. `get_complete_route` in `src/routing.py` is an empty stub with three comments, `Filter` in `src/filter.py` is an empty class, and the `/plan` endpoint in `src/server.py` therefore has nothing to call.

## What Changes

- Implement `get_complete_route(from_, to_, filters)` in `src/routing.py` as a three-stage trip: pick a disabled-parking spot near the destination, route by car from the origin to that spot, then route from the spot to the destination with the existing shade-optimized wheelchair logic.
- Give `Filter` real content: a filter constrains which parking spots are eligible, by spot attributes (owner, time restriction, status, disabled-parking type) and by a maximum remaining wheelchair distance from spot to destination. Filters combine with AND; an empty filter list accepts every spot.
- Select the spot by **shortest wheelchair leg among the nearest candidates**: gather all spots within a 500 m radius of the destination as candidates, apply the filters, narrow to the 5 closest by straight-line distance, then choose the candidate whose wheelchair route to the destination is shortest.
- Add a driving-car ORS leg (`.../v2/directions/driving-car/geojson`) reusing the existing `_post_ors` helper, auth, and error conventions.
- Return a single GeoJSON `FeatureCollection` in which the car→wheelchair switch is explicit: each leg feature carries a `mode` property (`driving-car` / `wheelchair`), and a dedicated `Point` feature marks the parking spot where the mode changes. This keeps the result shape compatible with `get_route` and `get_shade_wheelchair_route`, so `WebsiteBuilder.add_route` can render it unchanged.
- Expose the parking spots through `DatabaseHandler.get_all_parking_spots()` so callers never depend on the storage medium. For now that method is backed by the existing `data/layer*_wgs84.csv` exports rather than a populated SQLite database.
- Define failure behaviour: when no spot survives the radius plus filters, or no candidate is reachable by wheelchair, the call fails with a clear error instead of silently returning a single-mode route.

## Capabilities

### New Capabilities
- `parking-selection`: Choosing a disabled-parking spot near a destination — candidate gathering by radius, attribute and distance filtering, and ranking by wheelchair-leg length.

### Modified Capabilities
- `routing`: Adds a multi-modal (car-then-wheelchair) route requirement and the merged result format that makes the mode transfer visible. The existing wheelchair and shade requirements are unchanged and are reused as the second leg.

## Impact

- **Code**: `src/routing.py` (implement `get_complete_route`, add the driving-car leg and leg-merging), `src/filter.py` (real `Filter` model), `src/db_handler.py` (add `get_all_parking_spots`, CSV-backed for now), `src/coordinates.py` (a distance helper, if none is added locally to routing).
- **APIs**: One additional ORS profile in use (`driving-car`) on the already-configured openrouteservice host with the existing `ROUTING_API_KEY`. N+1 extra calls per request, where N is the number of filtered candidates evaluated for the wheelchair leg.
- **Data**: Reads `data/layer1_wgs84.csv` and `data/layer3_wgs84.csv` for positions and the corresponding `data/layer1.csv` / `data/layer3.csv` for attribute columns. `data/layer2.csv` is byte-identical to `layer1.csv` and is deliberately not read twice.
- **Dependencies**: none new.
- **Consumers**: `src/server.py` `/plan` becomes implementable; `src/server.py:29` already calls the not-yet-existing `DatabaseHandler.get_all_parking_spots()`, which this change provides.
- **Not affected**: `get_route` and `get_shade_wheelchair_route` keep their current signatures and behaviour.
