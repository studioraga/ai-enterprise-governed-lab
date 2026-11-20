#!/usr/bin/env bash
# Read-only Docker Engine diagnostics; safe on Node1, no service starts.
set -u
printf '\n== Docker client and context ==\n'
command -v docker || exit 2
docker version || true
docker context ls || true
printf '\n== Environment overrides ==\n'
for v in DOCKER_HOST DOCKER_CONTEXT XDG_RUNTIME_DIR; do
  if [[ ${!v+x} ]]; then printf '%s=%s\n' "$v" "${!v}"; else printf '%s=<unset>\n' "$v"; fi
done
printf '\n== Daemon unit status ==\n'
systemctl is-enabled docker.service docker.socket containerd.service 2>&1 || true
systemctl is-active docker.service docker.socket containerd.service 2>&1 || true
systemctl status docker.service docker.socket containerd.service --no-pager -l 2>&1 | tail -85 || true
printf '\n== Docker socket and packages ==\n'
ls -l /var/run/docker.sock /run/docker.sock 2>&1 || true
dpkg-query -W docker-ce docker-ce-cli containerd.io docker-compose-plugin 2>&1 || true
printf '\n== Kernel/runtime ==\n'
uname -a
stat -fc '%T' /sys/fs/cgroup 2>/dev/null || true
printf '\nDo NOT run Docker commands until docker info shows a Server section.\n'
