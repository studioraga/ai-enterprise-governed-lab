#!/usr/bin/env bash
# Read-only queries only. No Kubernetes Secret object values are retrieved.
set -euo pipefail
CTX="kind-${KIND_CLUSTER:-ai-enterprise-feasibility}"
NS="${LAB_NAMESPACE:-ai-enterprise-feasibility}"
APP="feasibility-api"
for x in kubectl jq; do command -v "$x" >/dev/null || { echo "BLOCKED: missing $x" >&2; exit 2; }; done
k() { kubectl --context "$CTX" --request-timeout=15s "$@"; }
k get --raw=/readyz >/dev/null
k -n "$NS" rollout status "deployment/$APP" --timeout=90s >/dev/null
SA="system:serviceaccount:$NS:$APP"
k -n "$NS" get sa "$APP" -o json | jq -e '.automountServiceAccountToken == false' >/dev/null || { echo 'FAIL: ServiceAccount token automount enabled' >&2; exit 1; }
k -n "$NS" get deploy "$APP" -o json | jq -e --arg sa "$APP" '
 .spec.template.spec.serviceAccountName == $sa and
 .spec.template.spec.automountServiceAccountToken == false and
 .spec.template.spec.securityContext.runAsNonRoot == true and
 .spec.template.spec.securityContext.runAsUser == 10001 and
 .spec.template.spec.securityContext.seccompProfile.type == "RuntimeDefault" and
 all(.spec.template.spec.containers[];
 .securityContext.allowPrivilegeEscalation == false and
 .securityContext.readOnlyRootFilesystem == true and
 (.securityContext.capabilities.drop | index("ALL") != null)) and
 all(.spec.template.spec.containers[]; (.env // [] | length) == 0 and (.envFrom // [] | length) == 0)
' >/dev/null || { echo 'FAIL: pod security or no-credential fixture contract differs' >&2; exit 1; }
for verb_resource in 'list secrets' 'create deployments'; do
  read -r verb resource <<< "$verb_resource"
  # kubectl returns "no" on authorization refusal; exit status varies by version.
  set +e
  output="$(k auth can-i "$verb" "$resource" --as="$SA" -n "$NS" 2>/dev/null)"
  rc=$?
  set -e
  if [[ "$output" != 'no' || "$rc" -gt 1 ]]; then
    echo "BLOCKED/FAIL: cannot establish denied $verb $resource (status=$rc, response=$output)" >&2; exit 1
  fi
  echo "PASS: serviceaccount denied $verb $resource"
done
# Inventory only: a missing Secret resource in the Helm chart is scope, not secret lifecycle acceptance.
echo 'PASS: dedicated tokenless ServiceAccount, non-root workload and no credential env references in current fixture'
echo 'NOT_APPLICABLE: application Secret provisioning for this no-secret fixture'
echo 'NOT_IMPLEMENTED: enterprise Secret rotation/revocation/managed CSI'
echo 'NOT_IMPLEMENTED: real OIDC/JWKS authentication'
echo 'WP1 independent acceptance PENDING; production authorization DENIED'
