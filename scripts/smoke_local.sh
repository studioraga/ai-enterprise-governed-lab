#!/usr/bin/env bash
set -euo pipefail
base="${BASE_URL:-http://127.0.0.1:18080}"
base="${base%/}"
check() {
  local name="$1" method="$2" url="$3" body="${4:-}" expected="$5" got
  if [[ "$method" == POST ]]; then
    got="$(curl --connect-timeout 3 --max-time 10 -sS -o /dev/null -w '%{http_code}' -X POST "$url" -H 'content-type: application/json' -d "$body")"
  else
    got="$(curl --connect-timeout 3 --max-time 10 -sS -o /dev/null -w '%{http_code}' "$url")"
  fi
  [[ "$got" == "$expected" ]] || { echo "FAIL $name: expected $expected got $got" >&2; return 1; }
  printf 'PASS %s: HTTP %s\n' "$name" "$got"
}
check livez GET "$base/livez" '' 200
check readyz GET "$base/readyz" '' 200
check cross_tenant POST "$base/demo/governed-read" \
  '{"subject":"demo-user","tenant":"a","resource_tenant":"b","action":"read_measurement","approved":true}' 403
check same_tenant POST "$base/demo/governed-read" \
  '{"subject":"demo-user","tenant":"a","resource_tenant":"a","action":"read_measurement","approved":true}' 200
printf 'NOTE: process readiness and synthetic request identity only; NOT OIDC or production isolation.\n'
