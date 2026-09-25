# Proposal

## Why

The CSV files in `data/` (`layer1.csv`, `layer2.csv`, `layer3.csv`) carry positions as `RECHTSWERT`/`HOCHWERT` — easting/northing in ETRS89 / UTM zone 32N (EPSG:25832), the standard German cadastral grid. Every other part of the project speaks WGS84 lat/lon via `Coordinates(lat, lon)` (`src/coordinates.py:4`), which is what the routing API in `src/routing.py` consumes. Until the grid coordinates are projected to lat/lon, this data cannot be used anywhere in the app.

## What Changes

- Add `pyproj` as a project dependency (installed with `uv add`).
- Add a conversion helper to `src/coordinates.py` that turns a UTM32 easting/northing pair into the existing `Coordinates` model.
- Add a CSV reader that parses the `data/layer*.csv` dialect (semicolon separator, comma decimal mark) and yields converted `Coordinates`.
- Add a small script that reads the three CSVs and writes converted copies with `lat`/`lon` columns, so the data is also usable outside Python.

Non-goals: no changes to routing, the server, or the website builder; the original CSVs are not modified in place, except for correcting one known data-entry typo in `data/layer3.csv` (see design.md).

## Capabilities

### New Capabilities
- `coordinate-conversion`: converting ETRS89 / UTM zone 32N grid coordinates from the project's CSV data into WGS84 latitude/longitude, including parsing the German CSV dialect and emitting converted CSV copies.

### Modified Capabilities

(none — no existing specs)

## Impact

- `src/coordinates.py` — gains conversion and CSV-loading functions alongside the existing `Coordinates` model.
- `pyproject.toml` / `uv.lock` — new `pyproj` dependency.
- New script for batch CSV conversion; new output files under `data/`.
- Existing consumers of `Coordinates` are unaffected; the model itself does not change.
