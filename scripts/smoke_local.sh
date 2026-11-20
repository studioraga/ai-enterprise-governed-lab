#!/usr/bin/env bash
set -euo pipefail
base="${BASE_URL:-http://127.0.0.1:18080}"
curl -fsS "$base/livez"
printf '\n'
status=$(curl -sS -o /dev/null -w '%{http_code}' -X POST "$base/demo/governed-read" -H 'content-type: application/json' -d '{"subject":"demo-user","tenant":"a","resource_tenant":"b","action":"read_measurement","approved":true}')
test "$status" = 403
printf 'PASS synthetic cross-tenant denial (HTTP 403)\n'
