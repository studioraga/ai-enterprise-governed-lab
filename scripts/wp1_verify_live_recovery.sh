#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
cluster="${KIND_CLUSTER:-ai-enterprise-feasibility}"
context="kind-${cluster}"
namespace="${LAB_NAMESPACE:-ai-enterprise-feasibility}"
release="${HELM_RELEASE:-feasibility}"
expected="ai-enterprise-feasibility:local"
for tool in docker kubectl helm jq; do command -v "$tool" >/dev/null || { echo "BLOCKED: missing $tool" >&2; exit 2; }; done
docker info >/dev/null || { echo 'BLOCKED: Docker daemon unavailable' >&2; exit 2; }
kubectl --context "$context" --request-timeout=10s get --raw=/readyz >/dev/null || { echo 'BLOCKED: Kubernetes API unreachable' >&2; exit 2; }
helm --kube-context "$context" -n "$namespace" history "$release" -o json | jq -e '
  any(.[]; .revision == 3) and
  any(.[]; .revision >= 4 and (.description | contains("Rollback to 2")))
' >/dev/null || { echo 'FAIL: expected rollback history not present' >&2; exit 1; }
helm --kube-context "$context" -n "$namespace" get manifest "$release" --revision 2 | grep -Fq "image: \"$expected\"" || { echo 'FAIL: revision 2 not known-good' >&2; exit 1; }
kubectl --context "$context" -n "$namespace" rollout status deployment/feasibility-api --timeout=120s
kubectl --context "$context" -n "$namespace" get deployment feasibility-api -o json | jq -e --arg image "$expected" '
 .metadata.generation == .status.observedGeneration and .spec.replicas == 1 and
 .status.updatedReplicas == 1 and .status.readyReplicas == 1 and
 .status.availableReplicas == 1 and .spec.template.spec.containers[0].image == $image
' >/dev/null
printf 'PASS: live rollback state and Deployment convergence; not full WP1 acceptance.\n'
