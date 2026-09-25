# Proposal

## Why

The project currently computes wheelchair-accessible routes in Python (`src/routing.py`), but the shade-aware combined routing logic only exists as a standalone bash script (`shade_wheelchair.sh`). This duplicated, shell-based implementation is hard to maintain, relies on a hardcoded auth token, and cannot be reused by the Flask server. Porting it into the Python codebase lets the server surface shade-optimized, wheelchair-accessible routes directly.

## What Changes

- Add a new `get_shaded_wheelchair_route(from_, to_)` function (or equivalent) to `src/routing.py`.
- Reimplement the two-stage workflow from `shade_wheelchair.sh` in Python using `requests`:
  1. Request a shade-optimized foot route from the shaded ORS instance (negative `csv_factor` on the shade raster column).
  2. Sample waypoints from that shaded path and feed them back into the standard wheelchair ORS profile with strict accessibility restrictions.
  3. On wheelchair failure, fall back to a plain wheelchair-accessible route.
- Return the result as a GeoJSON `FeatureCollection` (consistent with the existing `get_route`).
- Read API credentials from environment variables instead of the hardcoded token; support separate credentials/URLs for the shaded instance.

## Capabilities

### New Capabilities
- `routing`: Compute wheelchair-accessible routes. Extended by this change to also compute combined shade-optimized + wheelchair-accessible routes and to expose the shade/fallback behavior via a dedicated function.

### Modified Capabilities
- (none)

## Impact

- **Code**: `src/routing.py` gains a new function; existing `get_route` unchanged.
- **Config**: New environment variable(s) for the shaded ORS endpoint/credentials (e.g. `SHADED_ROUTING_API_KEY`, `SHADED_ROUTING_URL`).
- **Dependencies**: none new (uses existing `requests`, `geojson`).
- **Consumers**: future server endpoints / `server.py` can call the new function; bash script `shade_wheelchair.sh` remains but is superseded.
