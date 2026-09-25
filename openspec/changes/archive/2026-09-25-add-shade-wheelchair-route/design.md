# Design

## Context

`src/routing.py` currently exposes `get_route(from_, to_)` (see `src/routing.py:8`) that calls the ORS wheelchair profile with `requests` and returns a GeoJSON `FeatureCollection`. The shade+wheelchair algorithm exists only in the standalone bash script `shade_wheelchair.sh`. See proposal.md — Why.

The goal is a Python replacement that reuses the existing `requests`/`geojson` stack, reads credentials from the environment (as `get_route` already does via `os.environ["ROUTING_API_KEY"]`), and returns a GeoJSON object the server can hand to `WebsiteBuilder`.

## Goals / Non-Goals

**Goals:**
- Expose one new function in `src/routing.py` that returns a shade-optimized AND wheelchair-accessible route, with graceful fallback.
- Reuse the existing HTTP/`geojson` conventions; no shelling out to curl/jq.
- Read the shaded-instance credentials/URL from environment variables rather than embedding the hardcoded token from the bash script.

**Non-Goals:**
- Removing or modifying `shade_wheelchair.sh` or the existing `get_route`.
- Wiring the new function into `server.py` endpoints (left to a follow-up).
- Changing the strict wheelchair accessibility restrictions.

## Decisions

- **Single function `get_shade_wheelchair_route(from_: Coordinates, to_: Coordinates, num_waypoints: int = 12, shade_factor: float = -1) -> FeatureCollection`.** Mirrors the existing `get_route` signature/return type. The two ORS stages and the fallback live inside it, matching the SSH script's flow but expressed with `requests`.
- **Two HTTP stages via `requests.post`.** Stage 1 posts a foot-walking request to the shaded instance with a negative `csv_factor`/`csv_column` in `profile_params.weightings`; the shade bias is baked into `options`. Stage 2 samples waypoints from stage 1's coordinates and posts to the standard wheelchair profile with the same strict restrictions used by `get_route`.
- **Waypoint sampling in Python.** Replicates the SSH script's uniform sampling (step = `len//num`, ensure last point included) using list slicing rather than a `python3` subprocess.
- **Env-driven shaded endpoint.** Add `SHADED_ROUTING_URL` and `SHADED_ROUTING_API_KEY` new env vars; fall back to reusing `ROUTING_API_KEY` if the shaded key is unset, matching the shared-key convenience. The wheelchair stage always uses `ROUTING_API_KEY` (as `get_route` does). This removes the hardcoded token.
- **Fallback contract.** If the wheelchair stage through shaded waypoints returns non-200, call the plain wheelchair profile (existing `get_route` payload shape) and mark the result as fallback-dependent. If that also fails, raise an exception (the caller sees an error rather than a malformed route). Fallback mode is surfaced on the returned object so the caller can display "accessible only" vs "combined".
- **Reuse instead of new HTTP client.** `requests` is already a dependency and used in `routing.py`; introducing `httpx` or subprocess curl would add an unnecessary dependency.

*Alternatives considered:* keeping the bash script (rejected — not reusable by the server, hardcoded token); subprocess-wrapping the bash script (rejected — retains shell fragility); adding a new HTTP library (rejected — `requests` suffices).

## Risks / Trade-offs

- [Shaded ORS instance availability/rate limits] → Treat stage 1 failure as a non-200 error and surface it; consider a timeout mirroring the SSH script's `--max-time 180`.
- [Waypoint count tuning sways runtime/quality] → Make `num_waypoints` (and `shade_factor`) function parameters with the same defaults as the script (`12`, `-1`).
- [Two distinct keys/URLs to configure] → Provide env fallback so a single `ROUTING_API_KEY` still works for both if the shaded key is unset.
- [Hardcoded token removed could break environments relying on it] → The .env already supplies `ROUTING_API_KEY`; document the new vars in `.env.sample`.
