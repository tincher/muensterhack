# Spec Delta

## Purpose

Converts the ETRS89 / UTM zone 32N grid coordinates used by the project's German municipal CSV data into the WGS84 latitude/longitude pairs that the rest of the application works with.

## ADDED Requirements

### Requirement: Grid coordinates are converted to WGS84 latitude/longitude

The system SHALL convert an easting/northing pair expressed in ETRS89 / UTM zone 32N (EPSG:25832) into WGS84 latitude and longitude (EPSG:4326), returned as the project's existing coordinate representation of `lat` and `lon` in decimal degrees.

The conversion SHALL be accurate to within 1 metre of the authoritative EPSG:25832 → EPSG:4326 transformation.

#### Scenario: Converting a known Münster point

- **WHEN** the easting `406184.039` and northing `5757295.752` are converted
- **THEN** the result is latitude `51.9584` and longitude `7.6347`, each within 0.00001 degrees

#### Scenario: Conversion is a pure value transformation

- **WHEN** the same easting/northing pair is converted more than once
- **THEN** each call returns the same latitude/longitude, and no input data is modified

### Requirement: Municipal CSV data is parsed into coordinates

The system SHALL read the project's municipal CSV files and produce a converted WGS84 coordinate for each data row.

The reader SHALL handle the dialect used by these files: a header row, semicolon (`;`) field separator, and comma (`,`) as the decimal mark in numeric fields. Position columns SHALL be located by their header names `RECHTSWERT` (easting) and `HOCHWERT` (northing) rather than by column position, because the files differ in which other columns they contain.

The reader SHALL preserve each row's identifier (`LFDNR`) alongside the converted coordinate so a converted point can be traced back to its source row.

#### Scenario: Reading a file with the base column set

- **WHEN** `data/layer1.csv` is read
- **THEN** 232 coordinates are produced, one per data row, each with its `LFDNR` and a latitude/longitude within the Münster area (latitude between 51.85 and 52.1, longitude between 7.5 and 7.8)

#### Scenario: Reading a file with an extra column

- **WHEN** `data/layer3.csv` is read, which carries an additional `EIGENTUM` column before the position columns
- **THEN** the easting and northing are still taken from the `RECHTSWERT` and `HOCHWERT` columns, and the resulting coordinates fall within the same Münster area

#### Scenario: Values with and without a decimal part

- **WHEN** a row holds `406184,039` and another holds `405268` in a position column
- **THEN** both parse as the numbers `406184.039` and `405268` respectively

#### Scenario: A row cannot be converted

- **WHEN** a row has a missing or non-numeric value in a position column
- **THEN** the system reports which row failed and does not emit a silently wrong coordinate for it

### Requirement: Converted data can be exported as CSV

The system SHALL provide a way to write converted copies of the municipal CSV files, so the WGS84 coordinates are usable without running the application code.

Each output file SHALL contain the source row's identifier plus `lat` and `lon` columns in decimal degrees, use a standard comma-separated format with a period decimal mark, and SHALL be written alongside the source data without altering the original files.

`data/layer3.csv` carries one known data-entry error (row `LFDNR` 1709's `RECHTSWERT` had a stray leading digit, `3404159` instead of `404159`, placing it far outside Münster). This value was corrected directly in the source file as part of this change, since the reader has no reliable way to distinguish a corrupted-but-numeric value from a valid one. Aside from that single corrected value, source files are otherwise unmodified.

#### Scenario: Exporting all layers

- **WHEN** the export is run over `data/layer1.csv`, `data/layer2.csv`, and `data/layer3.csv`
- **THEN** one converted output file is written per source file, each with a header row followed by one row per source data row

#### Scenario: Source files are left intact

- **WHEN** the export has completed
- **THEN** `data/layer1.csv` and `data/layer2.csv` are byte-for-byte unchanged, and `data/layer3.csv` differs from its pre-change state only in the corrected `LFDNR` 1709 row
