#!/usr/bin/env bash
set -euo pipefail
printf 'Tool readiness (absence is NOT failure of WP0):\n'
for x in python3 git docker kubectl helm kind terraform aws az; do
  if command -v "$x" >/dev/null 2>&1; then printf 'FOUND %s: %s\n' "$x" "$(command -v "$x")"; else printf 'MISSING %s\n' "$x"; fi
done
python3 --version
