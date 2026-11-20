#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m compileall -q feasibility tests
python3 -m pytest -q tests
python3 scripts/verify_source_lock.py
python3 scripts/verify_project_identity.py
python3 scripts/check_no_production_claims.py
if command -v docker >/dev/null 2>&1; then docker compose config --quiet; else echo 'SKIP: Docker not installed'; fi
if command -v helm >/dev/null 2>&1; then helm lint helm/feasibility; helm template feasibility helm/feasibility >/dev/null; else echo 'SKIP: Helm not installed'; fi
printf 'WP0 local static + unit checks: PASS (conditional tool skips above)\n'

python3 scripts/verify_m0_compose_record.py
