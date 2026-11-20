#!/usr/bin/env bash
set -euo pipefail
# LAB ONLY. Creates a kind cluster if absent; no cloud deployment or production authorization.
cd "$(dirname "$0")/.."
cluster="${KIND_CLUSTER:-ai-enterprise-feasibility}"
namespace="${LAB_NAMESPACE:-ai-enterprise-feasibility}"
release="${HELM_RELEASE:-feasibility}"
image="ai-enterprise-feasibility:local"
context="kind-${cluster}"

for bin in docker kind kubectl helm; do
  command -v "$bin" >/dev/null 2>&1 || { printf 'BLOCKED: missing %s\n' "$bin" >&2; exit 2; }
done
# Reject unsafe Kubernetes target overrides. Always select the intended kind context.
case "$cluster" in *[!a-z0-9-]*|'' ) echo 'Invalid kind cluster name' >&2; exit 2;; esac
case "$namespace" in *[!a-z0-9-]*|'' ) echo 'Invalid namespace' >&2; exit 2;; esac

docker info >/dev/null || { echo 'BLOCKED: Docker daemon unavailable' >&2; exit 2; }
helm lint helm/feasibility
helm template "$release" helm/feasibility --namespace "$namespace" \
  --set image.repository=ai-enterprise-feasibility --set image.tag=local >/dev/null
if ! kind get clusters | grep -Fxq "$cluster"; then
  kind create cluster --name "$cluster"
fi
kubectl --context "$context" cluster-info >/dev/null
printf 'Confirmed LOCAL Kubernetes context: %s\n' "$context"
docker build --tag "$image" .
kind load docker-image "$image" --name "$cluster"
helm --kube-context "$context" upgrade --install "$release" helm/feasibility \
  --namespace "$namespace" --create-namespace \
  --set image.repository=ai-enterprise-feasibility \
  --set image.tag=local
kubectl --context "$context" -n "$namespace" rollout status \
  "deployment/${release}-api" --timeout=120s
kubectl --context "$context" -n "$namespace" get deployment,service,pods -o wide
printf '\nWP1 PARTIAL: deployment rollout checked. Smoke, isolation, secrets, network and rollback gates remain NOT_RUN.\n'
printf 'Context=%s Namespace=%s Release=%s Image=%s\n' "$context" "$namespace" "$release" "$image"
