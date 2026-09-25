# Design

## Context

See proposal.md — Why.

Current state: `src/coordinates.py` holds a six-line pydantic model, `Coordinates(lat, lon)`, already used as WGS84 throughout `src/routing.py`, `src/server.py`, and `src/park_sensor.py`. The three CSVs in `data/` each have 232 data rows. `layer1.csv` and `layer2.csv` share the columns `LFDNR;Z_BEGR1;STATUS;BEH_ART;RECHTSWERT;HOCHWERT`; `layer3.csv` inserts an extra `EIGENTUM` column, so `RECHTSWERT`/`HOCHWERT` sit at different indices. Numbers use a comma decimal mark, and some rows have no decimal part at all.

Constraint: the project has no geo/CRS dependency today and uses `uv` for dependency management.

## Goals / Non-Goals

**Goals:**
- One conversion function and one CSV reader, both in `src/coordinates.py`, next to the model they produce.
- A standalone script for batch-converting the CSVs.

**Non-Goals:**
- Wiring the converted data into routing, the server, or the website builder.
- Supporting UTM zones other than 32N or any CRS beyond EPSG:25832 → EPSG:4326.
- Reverse (lat/lon → UTM) conversion.

## Decisions

**Use `pyproj` rather than hand-rolling the inverse transverse Mercator formula.**
The Wikipedia series expansion is ~40 lines of easily mistyped math with no independent check on correctness. `pyproj` wraps PROJ, is the reference implementation for this transform, and reduces the conversion to one call. Cost is a binary wheel dependency (~6 MB), which is acceptable here. Added with `uv add pyproj`.

**Build the `Transformer` once at module level, not per call.**
`Transformer.from_crs` is comparatively expensive; the transform itself is cheap. A single module-level instance converts all 696 rows without repeated setup.

**Use `always_xy=True`.**
Without it, `pyproj` follows each CRS's declared axis order, so EPSG:4326 returns `(lat, lon)` while EPSG:25832 takes `(easting, northing)` — a silent swap that is easy to get wrong. `always_xy=True` makes both sides consistently `(x, y)` = `(easting, northing)` in and `(lon, lat)` out. Verified against four sample rows spanning the data's bounding box; all landed in Münster at 51.92–52.02°N, 7.52–7.73°E.

**Read CSVs with `csv.DictReader(delimiter=";")` and look up columns by header name.**
Index-based access would break on `layer3.csv`'s extra column. Decimal commas are handled by replacing `,` with `.` before `float()` — the files contain no thousands separators, so this is unambiguous.

**Write converted output to new `*_wgs84.csv` files rather than editing in place.**
The source CSVs are input data; keeping them untouched means the conversion can be re-run and diffed.

**Correct one data-entry typo directly in `data/layer3.csv` (`LFDNR` 1709, `RECHTSWERT` `3404159` → `404159`).**
Every other `RECHTSWERT` value in the three files is 6 digits (~398000–413000); this one had a stray leading `3`, producing a coordinate over 800 km from Münster. The reader can only detect missing or non-numeric values (spec requirement 3.4), not implausible-but-numeric ones, so this could not be caught programmatically without adding a plausibility/bounding-box check that isn't otherwise specified. Fixing the source value directly was simpler and keeps the exported data correct. This is the one exception to "source files are untouched."

## Risks / Trade-offs

- **Wrong source CRS assumption** → The values were checked against EPSG:25832 and resolve to Münster; a wrong zone or datum would place them hundreds of kilometres away, so the spec's bounding-box scenario catches this.
- **`pyproj` wheel availability on the target platform** → Wheels exist for CPython 3.13 on macOS and Linux; `uv add` resolves at lock time, so a failure surfaces immediately rather than at runtime.
- **Axis-order mistake produces plausible-looking output** → Mitigated by `always_xy=True` plus the fixed-point scenario in the spec, which pins one known easting/northing to its expected lat/lon.
