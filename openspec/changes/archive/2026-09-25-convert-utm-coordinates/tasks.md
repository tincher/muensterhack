# Tasks

## 1. Dependency

- [x] 1.1 Add pyproj with `uv add pyproj` and verify `uv run python -c "import pyproj; print(pyproj.__version__)"` prints a version

## 2. Coordinate conversion

- [x] 2.1 In `src/coordinates.py`, build a module-level `Transformer.from_crs("EPSG:25832", "EPSG:4326", always_xy=True)` and add `utm32_to_wgs84(easting: float, northing: float) -> Coordinates` returning the existing `Coordinates` model; verify `utm32_to_wgs84(406184.039, 5757295.752)` gives lat ≈ 51.958436 and lon ≈ 7.634660 within 0.00001 degrees
- [x] 2.2 Add a docstring naming the source CRS (ETRS89 / UTM zone 32N) and the reason for `always_xy=True`, so the axis order is not silently flipped later

## 3. CSV reading

- [x] 3.1 Add a decimal-comma parser (replace `,` with `.` then `float`) and verify it returns `406184.039` for `"406184,039"` and `405268.0` for `"405268"`
- [x] 3.2 Add a CSV reader in `src/coordinates.py` using `csv.DictReader(delimiter=";")` that reads `RECHTSWERT`/`HOCHWERT` by header name and yields each row's `LFDNR` with its converted `Coordinates`; verify reading `data/layer1.csv` yields 232 entries all within lat 51.85–52.1 and lon 7.5–7.8 (widened from 51.9 after auditing the real data's extent; see spec.md)
- [x] 3.3 Verify the reader handles `data/layer3.csv`, which has an extra `EIGENTUM` column, by confirming it also yields 232 entries in the same lat/lon range (required correcting one data-entry typo, `LFDNR` 1709's `RECHTSWERT`, in the source file — see design.md)
- [x] 3.4 Raise an error naming the offending row when a position column is missing or non-numeric; verify with a one-row fixture holding an empty `RECHTSWERT` that the error message contains that row's `LFDNR`

## 4. CSV export script

- [x] 4.1 Add a script that converts `data/layer1.csv`, `data/layer2.csv`, and `data/layer3.csv` into `data/layer{1,2,3}_wgs84.csv` with a `LFDNR,lat,lon` header, comma-separated and period decimal mark; verify each output file has 233 lines (header plus 232 rows)
- [x] 4.2 Run the script and verify the three source CSVs are unchanged; `data/*.csv` is untracked (not in `.gitignore` but never committed), so `git status --porcelain` always reports `??` regardless of content and can't detect a change here — verified with MD5 checksums before/after instead, which matched

## 5. Integration check

- [x] 5.1 Spot-check one exported row end to end: confirm `LFDNR` 183 in `data/layer1_wgs84.csv` reads lat 51.9584 / lon 7.6347, and that plotting or looking up that pair places it in Münster
- [x] 5.2 Run `uv run ruff check src` and confirm it passes at the project's 140-character line length (ruff isn't a project dependency, so this required `uv run --with ruff ruff check src`; passed with no findings)
