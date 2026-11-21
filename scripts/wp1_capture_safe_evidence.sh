#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
context="kind-${KIND_CLUSTER:-ai-enterprise-feasibility}"
namespace="${LAB_NAMESPACE:-ai-enterprise-feasibility}"
release="${HELM_RELEASE:-feasibility}"
out="reports/validation/wp1-safe-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$out"
# No kubeconfig, token, host environment dump, Docker inspect Env or raw Secrets in these outputs.
"$(dirname "$0")/wp1_verify_live_recovery.sh" > "$out/recovery-check.txt" 2>&1
helm --kube-context "$context" -n "$namespace" history "$release" > "$out/helm-history.txt"
kubectl --context "$context" -n "$namespace" get deployment,replicasets,pods,serviceaccount,networkpolicy -o wide > "$out/resources.txt"
kubectl --context "$context" -n "$namespace" get deployment feasibility-api -o json | jq '{name:.metadata.name,generation:.metadata.generation,observedGeneration:.status.observedGeneration,replicas:.spec.replicas,ready:.status.readyReplicas,updated:.status.updatedReplicas,available:.status.availableReplicas,image:.spec.template.spec.containers[0].image}' > "$out/deployment-summary.json"
cat > "$out/REVIEW_REQUIRED.txt" <<'EOF'
Evidence is from a single untrusted lab host. Review and redact manually before sharing.
Supplement with existing original failed-rollout logs and HTTP smoke logs.
Never package kubeconfig-before-recovery, Kubernetes tokens, Secrets, or unrestricted runtime exports.
NetworkPolicy enforcement, enterprise Secret lifecycle and independent approval: NOT_VERIFIED.
EOF
( cd "$out"; find . -maxdepth 1 -type f ! -name SHA256SUMS -print0 | sort -z | xargs -0 -r sha256sum > SHA256SUMS; sha256sum -c SHA256SUMS )
printf 'PARTIAL WP1 evidence stored: %s\n' "$out"
