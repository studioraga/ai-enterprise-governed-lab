#!/usr/bin/env bash
# M0 local-only Docker Compose qualification; does not authorize WP1 or production.
set -Eeuo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
project="${COMPOSE_PROJECT_NAME:-ai-enterprise-governed-lab}"
base="${BASE_URL:-http://127.0.0.1:18080}"
cleanup="${COMPOSE_CLEANUP:-0}"
[[ "$cleanup" == 0 || "$cleanup" == 1 ]] || { echo 'COMPOSE_CLEANUP must be 0 or 1' >&2; exit 2; }
for cmd in docker curl python3; do command -v "$cmd" >/dev/null || { echo "BLOCKED: $cmd unavailable" >&2; exit 2; }; done
case "$base" in http://127.0.0.1:18080|http://localhost:18080) ;; *) echo 'BLOCKED: BASE_URL must be local port 18080' >&2; exit 2;; esac
mkdir -p reports/validation
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
report="reports/validation/compose-${stamp}"
mkdir -p "$report"
printf '%s\n' "Evidence: $report"
printf 'Git commit: '; git rev-parse HEAD 2>/dev/null || true
python3 --version > "$report/python-version.txt"
docker --version > "$report/docker-cli.txt"
docker compose version > "$report/docker-compose-version.txt"
if ! docker info > "$report/docker-info.txt" 2> "$report/docker-daemon-error.txt"; then
  echo 'BLOCKED: Docker Engine daemon is unavailable. Inspect the saved error and systemctl status docker/containerd.' >&2
  sed -n '1,15p' "$report/docker-daemon-error.txt" >&2
  exit 2
fi
# Compose project is scoped to this lab only; no global prune or unrelated resource removal.
compose=(docker compose --project-name "$project")
"${compose[@]}" config --quiet
"${compose[@]}" config > "$report/compose-rendered.yaml"
# Avoid confusing an independently running local Uvicorn server with Compose.
if curl --fail --silent --max-time 2 "$base/livez" >/dev/null 2>&1; then
  if [[ "$("${compose[@]}" ps --status running -q api | wc -l)" -eq 0 ]]; then
    echo 'BLOCKED: port 18080 responds but this Compose project has no running API. Stop local uvicorn first.' >&2
    exit 2
  fi
fi
"${compose[@]}" build --pull api 2>&1 | tee "$report/build.log"
docker image inspect ai-enterprise-feasibility:local --format '{{.Id}} {{.Architecture}} {{.Os}}' > "$report/image.txt"
"${compose[@]}" up -d --no-build api 2>&1 | tee "$report/up.log"
"${compose[@]}" ps > "$report/ps.txt"
container_id="$("${compose[@]}" ps -q api)"
[[ -n "$container_id" ]] || { echo 'FAIL: API container not found' >&2; exit 1; }
status=''
for i in $(seq 1 30); do
  status="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}missing{{end}}' "$container_id")"
  [[ "$status" == healthy ]] && break
  [[ "$status" == unhealthy ]] && break
  sleep 2
done
printf '%s\n' "Container health: $status" | tee "$report/health.txt"
if [[ "$status" != healthy ]]; then
  "${compose[@]}" logs --no-color --tail=150 api > "$report/api.log" 2>&1 || true
  echo 'FAIL: Compose API never reached healthy' >&2
  exit 1
fi
for path in livez readyz; do
  code="$(curl -sS -o "$report/${path}.json" -w '%{http_code}' --max-time 5 "$base/$path")"
  [[ "$code" == 200 ]] || { echo "FAIL: $path returned $code" >&2; exit 1; }
done
BASE_URL="$base" bash scripts/smoke_local.sh 2>&1 | tee "$report/smoke.log"
"${compose[@]}" logs --no-color --tail=150 api > "$report/api.log" 2>&1
printf '%s\n' 'M0 DOCKER COMPOSE: PASS (not WP1/production)' | tee "$report/result.txt"
# Write checksums after all recorded files are complete.
(cd "$report" && sha256sum $(find . -maxdepth 1 -type f ! -name SHA256SUMS -printf '%f\n' | sort) > SHA256SUMS)
if [[ "$cleanup" == 1 ]]; then
  "${compose[@]}" down --remove-orphans
  echo 'Lab Compose resources stopped (volumes not deleted).'
else
  echo "Lab Compose resources left running; stop with: docker compose --project-name '$project' down"
fi
printf 'Evidence saved under %s\n' "$report"
