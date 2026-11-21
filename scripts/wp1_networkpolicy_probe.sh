#!/usr/bin/env bash
# WP1 disposable lab ONLY: differential ingress and egress NetworkPolicy probe.
# Creates exactly three disposable Pods and one namespace; does NOT auto-delete them.
set -euo pipefail
cd "$(dirname "$0")/.."
CTX="kind-${KIND_CLUSTER:-ai-enterprise-feasibility}"
NS="${LAB_NAMESPACE:-ai-enterprise-feasibility}"
PROBE_NS="ai-enterprise-wp1-probe"
CLIENT_IMAGE="${WP1_PROBE_IMAGE:-curlimages/curl:8.16.0}"
RECEIVER_IMAGE="${WP1_RECEIVER_IMAGE:-ai-enterprise-feasibility:local}"
APP="feasibility-api"
for tool in kubectl jq; do command -v "$tool" >/dev/null || { echo "BLOCKED missing $tool" >&2; exit 2; }; done
k() { kubectl --context "$CTX" --request-timeout=15s "$@"; }
k get --raw=/readyz >/dev/null
k -n "$NS" rollout status "deployment/$APP" --timeout=45s >/dev/null
k -n "$NS" get networkpolicy feasibility-api-deny-egress -o json | jq -e '
  .spec.podSelector.matchLabels.app == "feasibility-api" and
  (.spec.policyTypes | index("Ingress") != null and index("Egress") != null) and
  ((.spec.egress // []) | length == 0)
' >/dev/null || { echo 'BLOCKED: unexpected NetworkPolicy contract' >&2; exit 2; }
for item in "$NS/wp1-same-ns" "$NS/wp1-control-receiver" "$PROBE_NS/wp1-other-ns"; do
  ns="${item%%/*}"; pod="${item#*/}"
  if k -n "$ns" get pod "$pod" >/dev/null 2>&1; then
    echo "BLOCKED: existing probe Pod $item; review and clean prior attempt" >&2; exit 2
  fi
done
if k get namespace "$PROBE_NS" >/dev/null 2>&1; then
  echo "BLOCKED: existing probe namespace $PROBE_NS; inspect ownership" >&2; exit 2
fi
printf 'Cluster context: %s; application namespace: %s\n' "$CTX" "$NS"
printf 'Client image: %s; receiver image: %s\n' "$CLIENT_IMAGE" "$RECEIVER_IMAGE"
k create namespace "$PROBE_NS"
k -n "$NS" run wp1-same-ns --image="$CLIENT_IMAGE" --restart=Never --command -- sleep 1800
k -n "$PROBE_NS" run wp1-other-ns --image="$CLIENT_IMAGE" --restart=Never --command -- sleep 1800
# Give the disposable control receiver its own HTTP readinessProbe. A Pod with no
# readinessProbe can report Ready before Uvicorn accepts connections.
# No default ServiceAccount token or unnecessary privilege is granted.
cat <<EOF | k -n "$NS" apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: wp1-control-receiver
  labels:
    app: wp1-control-receiver
    app.kubernetes.io/part-of: ai-enterprise-governed-lab-wp1-probe
spec:
  restartPolicy: Never
  automountServiceAccountToken: false
  securityContext:
    runAsNonRoot: true
    runAsUser: 10001
    runAsGroup: 10001
    seccompProfile:
      type: RuntimeDefault
  containers:
    - name: receiver
      image: ${RECEIVER_IMAGE}
      imagePullPolicy: IfNotPresent
      ports:
        - name: http
          containerPort: 8000
      startupProbe:
        httpGet:
          path: /livez
          port: http
        periodSeconds: 2
        failureThreshold: 30
      readinessProbe:
        httpGet:
          path: /readyz
          port: http
        periodSeconds: 2
        timeoutSeconds: 2
      securityContext:
        readOnlyRootFilesystem: true
        allowPrivilegeEscalation: false
        capabilities:
          drop: [ALL]
      resources:
        requests: {cpu: 10m, memory: 32Mi}
        limits: {cpu: 250m, memory: 256Mi}
EOF
for entry in "$NS/wp1-same-ns" "$PROBE_NS/wp1-other-ns" "$NS/wp1-control-receiver"; do
  ns="${entry%%/*}"; pod="${entry#*/}"
  k -n "$ns" wait --for=condition=Ready "pod/$pod" --timeout=120s || {
    echo "BLOCKED: $entry not ready; inspect image, logs and scheduling" >&2; exit 2;
  }
done
APP_IP="$(k -n "$NS" get pods -l app="$APP" -o json | jq -r '[.items[] | select(.status.phase=="Running" and ([.status.conditions[]? | select(.type=="Ready" and .status=="True")] | length) > 0) | .status.podIP] | first // empty')"
CONTROL_IP="$(k -n "$NS" get pod wp1-control-receiver -o jsonpath='{.status.podIP}')"
[[ "$APP_IP" =~ ^[0-9]+(\.[0-9]+){3}$ && "$CONTROL_IP" =~ ^[0-9]+(\.[0-9]+){3}$ ]] || { echo 'BLOCKED: missing IPv4 Pod IPs' >&2; exit 2; }
# Require the receiver process to answer locally before interpreting any network
# restrictions. Pod readiness alone should not silently qualify TCP reachability.
k -n "$NS" exec wp1-control-receiver -- python -c 'import urllib.request; assert urllib.request.urlopen("http://127.0.0.1:8000/livez", timeout=3).status == 200' || {
  echo 'BLOCKED: control receiver did not answer HTTP on loopback; inspect its logs and Pod events' >&2; exit 2;
}
printf 'Protected Pod IPv4: %s; control receiver IPv4: %s\n' "$APP_IP" "$CONTROL_IP"
curl_from() {
  local namespace="$1" pod="$2" ip="$3"
  k -n "$namespace" exec "$pod" -- curl -4 --silent --show-error --connect-timeout 2 --max-time 5 -o /dev/null -w '%{http_code}' "http://${ip}:8000/livez"
}
expect_200() {
  local what="$1" namespace="$2" pod="$3" ip="$4" result
  result="$(curl_from "$namespace" "$pod" "$ip")" || { echo "FAIL: $what control failed" >&2; exit 1; }
  [[ "$result" == '200' ]] || { echo "FAIL: $what expected 200, got $result" >&2; exit 1; }
  echo "PASS: $what HTTP 200"
}
expect_timeout() {
  local what="$1" namespace="$2" pod="$3" ip="$4" result rc
  set +e
  result="$(curl_from "$namespace" "$pod" "$ip" 2>&1)"
  rc=$?
  set -e
  if [[ "$rc" != 28 ]]; then
    echo "FAIL: $what expected curl timeout exit 28; got exit=$rc: $result" >&2; exit 1
  fi
  printf 'PASS: %s; curl timeout exit 28\n' "$what"
}
# All three positive controls precede security-denial assertions.
expect_200 'same namespace to protected Pod' "$NS" wp1-same-ns "$APP_IP"
expect_200 'same namespace to unprotected control receiver' "$NS" wp1-same-ns "$CONTROL_IP"
expect_200 'other namespace to unprotected control receiver' "$PROBE_NS" wp1-other-ns "$CONTROL_IP"
expect_timeout 'other namespace to protected Pod ingress denied' "$PROBE_NS" wp1-other-ns "$APP_IP"
# Use Python already in the protected workload, and demand socket.timeout specifically;
# a missing command, DNS failure, HTTP error or connection refusal is a FAIL.
EGRESS_RESULT="$(k -n "$NS" exec "deployment/$APP" -- python -c '
import socket, sys
ip=sys.argv[1]
try:
    sock=socket.create_connection((ip,8000), timeout=4)
except socket.timeout:
    print("DENIED_TIMEOUT")
    sys.exit(0)
except OSError as exc:
    print("UNEXPECTED_ERROR: " + repr(exc), file=sys.stderr)
    sys.exit(2)
else:
    sock.close()
    print("UNEXPECTED_CONNECTION_SUCCEEDED",file=sys.stderr)
    sys.exit(3)
' "$CONTROL_IP")" || { echo 'FAIL: protected Pod egress probe returned an unexpected error' >&2; exit 1; }
[[ "$EGRESS_RESULT" == 'DENIED_TIMEOUT' ]] || { echo "FAIL: unexpected egress result: $EGRESS_RESULT" >&2; exit 1; }
echo 'PASS: protected application egress denied (socket timeout)'
k -n "$NS" rollout status "deployment/$APP" --timeout=45s >/dev/null
echo 'BEHAVIORAL PASS: three positive HTTP controls and both selected-denial paths verified; independent review still required.'
echo "RETAIN FOR REVIEW: Pods $NS/wp1-same-ns, $NS/wp1-control-receiver; namespace $PROBE_NS."
echo "CLEANUP: kubectl --context '$CTX' -n '$NS' delete pod wp1-same-ns wp1-control-receiver"
echo "CLEANUP: kubectl --context '$CTX' delete namespace '$PROBE_NS'"
