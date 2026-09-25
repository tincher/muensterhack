#!/usr/bin/env bash
#
# shade_wheelchair.sh
#
# Find a single routing path that is BOTH wheelchair-accessible AND in the shade.
#
# Strategy:
#   1. Ask the shade-enabled ORS instance for a foot route that is biased toward
#      shade (negative csv_factor on the shade raster column). This yields a path
#      that hugs shaded streets.
#   2. Feed representative waypoints of that shaded path back into the standard
#      ORS wheelchair profile (with strict accessibility restrictions) so it
#      routes A -> waypoint_1 -> ... -> B while staying usable by a wheelchair.
#   3. Result: a single route that is accessible and follows the shaded path.
#      If no such accessible route can be found, fall back to the plain
#      wheelchair-accessible route.
#
# Usage:
#   ./shade_wheelchair.sh <start_lon> <start_lat> <end_lon> <end_lat>
#
# Example:
#   ./shade_wheelchair.sh 7.638082 51.950745 7.634425163269044 51.95606190419299
#
# Outputs:
#   shade_wheelchair.geojson  - the combined route (success) or wheelchair route (fallback)
#   Prints a summary and turn-by-turn instructions to stdout.
#
# Dependencies: curl, jq, python3

set -euo pipefail

AUTH="eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6Ijg4OGNmZWFhZGYwNTQ4MzA5MGE0MDc3Y2Q4MWFmMjBlIiwiaCI6Im11cm11cjY0In0="

SHADE_URL="https://api.shaded.openrouteservice.org/ors/v2/directions/foot-walking/geojson"
WHEELCHAIR_URL="https://api.openrouteservice.org/v2/directions/wheelchair/geojson"

# Shade raster column used by the shaded instance (higher = more shade).
SHADE_COLUMN="233_18"
# Negative factor biases routing toward higher shade values. Tune magnitude:
# stronger (e.g. -3) = shadier but slower to compute.
SHADE_FACTOR="${SHADE_FACTOR:--1}"
# How many waypoints to sample from the shade path (more = stricter adherence).
NUM_WAYPOINTS="${NUM_WAYPOINTS:-12}"

# Wheelchair accessibility restrictions (strict).
RESTRICTIONS='{
    "maximum_incline": "6",
    "maximum_sloped_kerb": "0.06",
    "minimum_width": 1,
    "smoothness_type": "good",
    "surface_type": "cobblestone",
    "track_type": "grade1"
}'
ALLOW_UNSUITABLE="${ALLOW_UNSUITABLE:-False}"   # Python bool: False or True

usage() {
    echo "Usage: $0 <start_lon> <start_lat> <end_lon> <end_lat>"
    exit 1
}

# [[ $# -eq 4 ]] || usage
# START_LON="$1"; START_LAT="$2"; END_LON="$3"; END_LAT="$4"
START_LON="7.641"; START_LAT="51.952"; END_LON="7.626"; END_LAT="51.962"

curl_hdr=(-sS --max-time 180 -H "Authorization: $AUTH" -H "Content-type: application/json")

echo "==> Requesting shade-optimized route from Shaded ORS ..."
SHADE_PAYLOAD=$(python3 - "$START_LON" "$START_LAT" "$END_LON" "$END_LAT" "$SHADE_FACTOR" "$SHADE_COLUMN" <<'PY'
import json, sys
slon, slat, elon, elat, factor, col = sys.argv[1:7]
print(json.dumps({
  "coordinates":[[float(slon),float(slat)],[float(elon),float(elat)]],
  "elevation":True,
  "instructions_format":"text",
  "language":"en",
  "units":"km",
  "preference":"recommended",
  "options":{
    "profile_params":{"weightings":{"csv_factor":float(factor),"csv_column":col}},
    "avoid_features":["ferries"]
  }
}))
PY
)

HTTP=$(curl "${curl_hdr[@]}" -o /tmp/shade_response.json -w "%{http_code}" \
    -X POST "$SHADE_URL" --data "$SHADE_PAYLOAD")

if [[ "$HTTP" != "200" ]]; then
    echo "ERROR: shade API returned HTTP $HTTP:" >&2
    cat /tmp/shade_response.json >&2
    exit 1
fi

SHADE_COUNTS=$(jq '.features[0].geometry.coordinates | length' /tmp/shade_response.json)
echo "    Shade route found with $SHADE_COUNTS geometry points."
echo "    Sampling $NUM_WAYPOINTS waypoints to enforce in the wheelchair route ..."

WAYPOINTS=$(python3 - "$NUM_WAYPOINTS" /tmp/shade_response.json <<'PY'
import json, sys
num = int(sys.argv[1])
coords=json.load(open(sys.argv[2]))["features"][0]["geometry"]["coordinates"]
step=max(1, len(coords)//num)
wps=[p[:2] for p in coords[::step]]
if wps[-1] != coords[-1][:2]:
    wps.append(coords[-1][:2])
print(json.dumps(wps))
PY
)

echo "==> Requesting wheelchair-accessible route through the shaded waypoints ..."
WHEEL_PAYLOAD=$(python3 - "$WAYPOINTS" "$RESTRICTIONS" "$ALLOW_UNSUITABLE" <<'PY'
import json, sys
wps = json.loads(sys.argv[1])
restrictions = json.loads(sys.argv[2])
allow = sys.argv[3] == "True"
print(json.dumps({
  "coordinates": wps,
  "elevation": True,
  "instructions_format": "text",
  "language": "en",
  "units": "km",
  "preference": "recommended",
  "options": {"profile_params": {
      "restrictions": restrictions,
      "surface_quality_known": False,
      "allow_unsuitable": allow
  }}
}))
PY
)

HTTP=$(curl "${curl_hdr[@]}" -o /tmp/wheel_response.json -w "%{http_code}" \
    -X POST "$WHEELCHAIR_URL" --data "$WHEEL_PAYLOAD")

if [[ "$HTTP" != "200" ]]; then
    echo "    Wheelchair route through shaded waypoints failed (HTTP $HTTP)."
    echo "    Falling back to a plain wheelchair-accessible route ..."
    FALLBACK_PAYLOAD=$(python3 - "$START_LON" "$START_LAT" "$END_LON" "$END_LAT" "$RESTRICTIONS" "$ALLOW_UNSUITABLE" <<'PY'
import json, sys
slon, slat, elon, elat = sys.argv[1:5]
restrictions = json.loads(sys.argv[5])
allow = sys.argv[6] == "True"
print(json.dumps({
  "coordinates":[[float(slon),float(slat)],[float(elon),float(elat)]],
  "elevation": True,
  "instructions_format": "text",
  "language": "en",
  "units": "km",
  "preference": "recommended",
  "options": {"profile_params": {"restrictions": restrictions,
      "surface_quality_known": False, "allow_unsuitable": allow}}
}))
PY
)
    HTTP=$(curl "${curl_hdr[@]}" -o /tmp/wheel_response.json -w "%{http_code}" \
        -X POST "$WHEELCHAIR_URL" --data "$FALLBACK_PAYLOAD")
    if [[ "$HTTP" != "200" ]]; then
        echo "ERROR: wheelchair API returned HTTP $HTTP:" >&2
        cat /tmp/wheel_response.json >&2
        exit 1
    fi
    MODE="fallback (accessible only, not shade-optimized)"
else
    MODE="combined (shade-optimized + wheelchair-accessible)"
fi

OUT_FILE="$(cd "$(dirname "$0")" && pwd)/shade_wheelchair.geojson"
cp /tmp/wheel_response.json "$OUT_FILE"
echo
echo "================================================================================"
echo " Route mode : $MODE"
echo "================================================================================"
jq -r '
  .features[0].properties as $p |
  " Distance   : \($p.summary.distance) km",
  " Duration   : \($p.summary.duration) s",
  " Ascent     : \($p.ascent) m",
  " Descent    : \($p.descent) m",
  " Warnings   : \((($p.warnings // []) | map(.message) | join("; ")) // "none")",
  "",
  "Turn-by-turn (removed HTML tags):"
' /tmp/wheel_response.json
jq -r '.features[0].properties.segments[].steps[] | "  \(.instruction | gsub("<[^>]*>";""))  (\(.distance) km, \(.duration)s)"' /tmp/wheel_response.json
echo
echo "Route GeoJSON written to: $OUT_FILE"
