# Design

## Context

See proposal.md — Why. The relevant current state:

- `src/routing.py` already has `_post_ors(url, payload, api_key)` (raises `RuntimeError` on non-200), `_wheelchair_payload(...)`, `_sample_waypoints(...)`, and `get_shade_wheelchair_route(...)`, which returns a GeoJSON `FeatureCollection` and sets `route["route_mode"] = "combined" | "fallback"`.
- An ORS route response is a `FeatureCollection` with exactly **one** `LineString` feature; `properties.summary` holds `{distance, duration}` (distance in km, since payloads set `units: "km"`), and `properties.segments[]` holds the turn-by-turn steps.
- `WebsiteBuilder.add_route(data)` (`src/website_builder.py:33`) hands the object straight to `L.geoJSON(...)`, so any valid `FeatureCollection` renders.
- Parking data: `data/layer1_wgs84.csv` and `data/layer3_wgs84.csv` carry `LFDNR,lat,lon`; the matching `data/layer1.csv` / `data/layer3.csv` carry the attributes. Measured: `layer2.csv` is byte-identical to `layer1.csv`, and the `LFDNR` sets of layer1 and layer3 are disjoint — 464 spots in total.
- Attribute value space measured from the data: `STATUS` is always `A`; `BEH_ART` is always `10`; `Z_BEGR1` ∈ {`N`, `J`, empty}; `EIGENTUM` (layer3 only) ∈ {`PRI`, `NRW`, `UNI`, `KIR`, `KRA`, `BUND`, `STF`, `WHN`, `VER`, `DB`}.
- Measured candidate density: a 500 m radius around the example destination contains **43** spots; the worst case across all 464 spots as destination is 42, median 8.
- Measured ORS behavior: the wheelchair matrix endpoint does not return a per-pair `null` for a point that cannot be snapped onto the wheelchair network at all — it fails the **entire** call with HTTP 500 (`"Some target nodes could not be found"`). For the example destination, 15 of the 43 in-radius candidates trigger this; the failure persists even at a 300 m radius (3 of 12 candidates). A `null` entry is only returned for pairs that snap but have no connecting route (confirmed separately with an off-network stub point). This makes "matrix over every in-radius candidate" unreliable as the primary path — it fails for the very destination the design was built around.

That density is the central constraint. "Pick the spot with the shortest wheelchair route" over 43 candidates, if done with one routing call each, is 43 calls — and with the shade logic each of those is 2 calls. That is not viable per request. The snapping failure above is the second constraint: even the one-matrix-call approach cannot span all in-radius candidates reliably, so ranking is restricted to a small, fixed-size pool instead.

## Goals / Non-Goals

**Goals:**

- Keep the per-request ORS call count roughly constant (~3) regardless of how many candidates fall inside the radius.
- Reuse the existing `_post_ors` / payload / `RuntimeError` conventions rather than introducing a second HTTP style.
- Make the result a drop-in for the existing single-mode results so `WebsiteBuilder` needs no change.
- Keep `routing.py` ignorant of where parking spots are stored.

**Non-Goals:**

- Populating the SQLite database or writing `scripts/fill_db.py` — `DatabaseHandler.get_all_parking_spots()` is CSV-backed in this change; only its internals change later.
- Wiring `/plan` in `src/server.py` (left to a follow-up; this change only makes it possible).
- Live occupancy. Only one real sensor exists (`SENSOR_ID = 677`), so an occupancy filter would be arbitrary for the other 463 spots.
- Changing `get_route` or `get_shade_wheelchair_route`.

## Decisions

**1. Narrow to the 5 straight-line-nearest eligible candidates, then rank those with one ORS Matrix call.**
Filtering by radius alone leaves up to 42 candidates, and — per the measured snapping failure above — a matrix call spanning all of them is unreliable regardless of count: one ungraphable point anywhere in the batch fails the whole call. Capping to the 5 candidates closest by straight-line distance keeps the batch small enough that this is rare in practice and bounds the damage (and the fallback cost) when it still happens. `POST /v2/matrix/wheelchair` with `locations = [<narrowed candidate 1..5>, <destination>]`, `sources = [0..4]`, `destinations = [5]`, `metrics: ["distance"]` returns each of the 5 candidates' wheelchair network distance to the destination in one request. Pick the minimum, then compute the *real* route only for the winner. Total: 1 matrix + 1 car + 1 shade-wheelchair (itself 2 calls) ≈ 4 calls, flat.
*Alternatives:* one route call per candidate (rejected — 43+ calls, seconds of latency, rate-limit risk); matrix over every in-radius candidate (rejected — measured to fail entirely on real data whenever an ungraphable point is present, which happens for the example destination); straight-line nearest with no wheelchair ranking at all (rejected — the user explicitly asked for shortest wheelchair, and straight-line ignores the barriers that matter most to a wheelchair user).
*Trade-off accepted:* the true shortest-wheelchair-route candidate could theoretically lie outside the 5 closest by straight line (e.g. the 6th-nearest has a much shorter accessible route than the 5 nearest). Given the measured median of 8 and worst case of 42 in-radius candidates, and no way to span all of them in one reliable call, 5 is the bound that stayed reliable in testing; the spec is revised to match this real guarantee.

**2. Matrix distance ranks; the shade route is computed once, for the winner only.**
The matrix uses the plain wheelchair profile, so the ranking reflects accessible network distance, not shade. Shade is a comfort preference applied to the leg actually travelled — optimizing the *choice of spot* for shade would need a matrix per shade variant. The spec requires shortest wheelchair route, which is what the matrix measures.

**3. Matrix failure falls back to routing the same narrowed candidates individually.**
If the matrix call fails (including the whole-call snapping failure above) or the profile is unavailable, fall back to computing a plain wheelchair route for each of the same 5 narrowed candidates individually and taking the shortest. Same pool, same selection semantics, bounded cost (≤5 extra calls), no hard dependency on the matrix endpoint succeeding.

**4. Unroutable candidates are skipped via `null` matrix entries.**
ORS returns `null` for unreachable pairs. Drop those, then take the min of what remains. This satisfies "skip an unroutable candidate" without extra calls. If every entry is `null`, raise.

**5. `Filter` is a pydantic model with optional fields, ANDed.**
Matches the project's existing pydantic use (`Coordinates`, `ParkSensor`). Fields: `owner`, `time_restricted`, `status`, `parking_type`, `max_wheelchair_distance_m` — all optional, `None` meaning "unconstrained". A `matches(spot)` method covers the attribute fields; `max_wheelchair_distance_m` cannot be evaluated there because it needs the routed distance, so it is applied as a post-matrix cutoff. This split is deliberate: attribute filters run before any network call (the spec requires ineligible spots to cost no routing work), the distance filter runs against matrix output that was already fetched in bulk.
*Alternative:* a callable/predicate `Filter` (rejected — not serializable, and the distance constraint could not be split into a cheap and an expensive phase).

**6. `ParkingSpot` is a pydantic model owned by `db_handler.py`.**
Carries `id`, `coordinates: Coordinates`, and the four attributes. `routing.py` imports it; `filter.py` matches against it. Putting it in `db_handler.py` keeps the store as the thing that defines what a spot is.

**7. `get_all_parking_spots()` reads layer1 + layer3 only, joining attributes by `LFDNR`.**
`layer2.csv` is skipped as a verified byte-identical duplicate of `layer1.csv`. Attributes come from the original semicolon/comma-decimal CSVs via the existing `read_municipal_csv` conventions in `src/coordinates.py`; positions come from the already-exported `_wgs84.csv` files. De-duplication by `LFDNR` is still applied defensively, since the spec requires it and the source files could change. `EIGENTUM` is absent in layer1 — represent it as `None`, which a filter for a specific owner will then not match.

**8. Distance uses `pyproj.Geod` (already a dependency).**
`Geod(ellps="WGS84").inv(...)` gives true ellipsoidal metres for the radius test. No new dependency, no hand-rolled haversine.

**9. Result shape: one `FeatureCollection`, three features.**
`[car LineString, wheelchair LineString, transfer Point]`. Each `LineString` gets `properties.mode` (`"driving-car"` / `"wheelchair"`) plus its original ORS `properties` (so `summary.distance` / `summary.duration` per leg stay available, satisfying the "journey totals" scenario). The `Point` sits at the parking spot with `properties = {"type": "transfer", "mode_from": "driving-car", "mode_to": "wheelchair", "parking_spot_id": ...}`. Top level carries `route_mode = "complete"`, consistent with the existing `"combined"` / `"fallback"` marker, and `parking_spot_id`. The wheelchair leg's own `route_mode` from `get_shade_wheelchair_route` is preserved as `properties.shade_mode` so a shade fallback is still visible.
*Alternative:* a dict of two separate FeatureCollections (rejected — not compatible with the other functions' return shape, and `add_route` could not render it directly). Merging the two `LineString`s into one geometry (rejected — erases exactly the transfer the user asked to make visible).

**10. The car leg reuses `_post_ors` against `/v2/directions/driving-car/geojson`.**
Same host, same `ROUTING_API_KEY`. `units: "km"` and `instructions_format: "html"` to match `get_route`. No `elevation` — irrelevant for a car and it inflates the payload.

**11. Failures raise `RuntimeError`, never degrade to a single-mode route.**
Distinct messages for "no spot in radius", "no spot passed filters", "no spot reachable", so a caller can tell them apart. Matches the existing `_post_ors` failure style and the spec's prohibition on substituting a single-mode result.

## Risks / Trade-offs

- **A matrix call fails entirely (HTTP 500) if any location in the batch cannot be snapped onto the wheelchair network** → Measured, not hypothetical: 15 of 43 in-radius candidates for the example destination trigger this, and it still occurs at a 300 m radius. Mitigated by narrowing to 5 candidates before the matrix call (Decision 1) and by the per-candidate fallback (Decision 3), which routes each of the same 5 individually and so is unaffected by a batch-wide failure.
- **Ranking no longer considers every in-radius candidate, only the 5 nearest by straight line** → A candidate ranked 6th or later by straight line is never evaluated for its wheelchair distance, even if its route would be shorter than the 5 considered. Accepted trade-off: the measured matrix failure means there is no reliable way to rank an unbounded in-radius set in one call, and 5 is the size that stayed reliable in testing (worst case measured: 3 of 12 candidates ungraphable at 300 m). The spec's "shortest wheelchair leg" guarantee is now explicitly scoped to the 5 nearest by straight line, not to every candidate in the radius.
- **Ranking by distance ignores duration** → Wheelchair speed is near-constant in ORS, so distance and duration rank almost identically; distance is also the unit the `max_wheelchair_distance_m` filter is expressed in, so one metric serves both.
- **Matrix distance and the final shade route distance will differ** (the shade route detours for shade) → The matrix value is used only for ranking and for the distance cutoff; the returned route reports its own real summary. If the cutoff must hold for the *actual* travelled leg, re-check it after the shade route and raise. Document that the filter is evaluated on the direct wheelchair distance.
- **A private (`PRI`) spot may be unusable in practice** → 153 of 464 spots are `PRI`. Not silently excluded, since only the caller knows their entitlement; exposing `owner` as a filter field is the mitigation.
- **layer1 spots have no `EIGENTUM`** → An owner filter silently drops all 232 of them. Mitigated by treating `None` as "unknown" and documenting that an owner filter restricts to layer3 spots.
- **~4 sequential ORS calls per request** → Latency roughly doubles versus a single-mode route. Acceptable for an on-demand trip planner; the matrix decision is what keeps it from being ~45.
- **No automated tests exist in this repo** → Verification stays manual (`__main__` smoke block plus `ruff`), consistent with the two archived changes.

## Open Questions

- Whether `/plan` should expose the filter set as query parameters or a POST body. Deferrable: it does not affect this change's function signature, specs, or tasks.
