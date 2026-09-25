# Tasks

## 1. Environment configuration

- [x] 1.1 Add `SHADED_ROUTING_URL` and `SHADED_ROUTING_API_KEY` placeholders to `.env.sample` and verify `.env` loads them via `python-dotenv` (used in `src/server.py`)

## 2. Core implementation in src/routing.py

- [x] 2.1 Add a `get_shade_wheelchair_route` function that posts a foot-walking request to the shaded ORS instance with a negative `csv_factor` on the shade raster column, and verify it returns a 200 GeoJSON response (mirror `get_route`'s `requests`/auth/`geojson.loads` conventions)
- [x] 2.2 Add waypoint sampling (uniform step from the shade path coordinates, ensuring the final point is included) and re-post the sampled waypoints through the wheelchair ORS profile with the same strict restrictions as `get_route`, and verify it returns a GeoJSON FeatureCollection
- [x] 2.3 Add fallback: on wheelchair non-200, call the plain wheelchair route; if that also fails, raise an error; mark the returned object so the caller can tell "combined" from "fallback", and verify both branches behave correctly under simulated HTTP statuses
- [x] 2.4 Add a `if __name__ == "__main__"` smoke block (extending the existing one) that calls `get_shade_wheelchair_route` with the example coordinates and prints the returned route, and verify it runs end-to-end

## 3. Integration verification

- [x] 3.1 Run `ruff` (line-length 140 per pyproject) and `python -c "import src.routing"` and confirm no lint/import errors
