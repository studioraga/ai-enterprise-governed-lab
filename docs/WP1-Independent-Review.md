# WP1 independent lab review — November 21, 2026

**Boundary:** M0 remains accepted; WP1 is in progress, independent approval pending, and production authorization denied. This document is a review procedure, not an approval receipt.

## Reviewed Node1 test history

- Helm chart Deployment/Service/ServiceAccount/NetworkPolicy rendered and applied to the owned kind cluster.
- Helm revision 3 deliberately used `missing-test-image`; kubelet recorded image-pull failure. After the Node1 reboot, the original cluster was recovered; Helm revision 4 rolled back to revision 2; application restored and returned HTTP 200/200/403/200.
- v5.2 network probe failed a positive control with `curl (7)` because the control receiver was not yet accepting HTTP. It was not classified as a policy denial.
- v5.3 improved the control receiver with startup/readiness probes. The November 21 evidence directory `reports/validation/wp1-network-v5.3-20261121T052723Z/` records **three HTTP-200 controls**, a curl 28 timeout from the other namespace, a socket timeout from the protected Pod, and a zero exit code. The receiver was Ready; its application logs show HTTP requests from both test clients. An initial startup-probe connection-refused warning resolved before traffic tests.
- The live ServiceAccount was tokenless; `kubectl auth can-i` output was `no` for listing Secrets and creating Deployments. Kubernetes had one ready application replica after probe cleanup.

## Offline evidence assessment (do not edit the original hashed bundle)

```bash
EVIDENCE=reports/validation/wp1-network-v5.3-20261121T052723Z
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
REVIEW="reports/validation/wp1-review-${STAMP}"
mkdir -p "$REVIEW"
python3 scripts/wp1_review_network_evidence.py \
  --evidence "$EVIDENCE" \
  --source scripts/wp1_networkpolicy_probe.sh \
  --output "$REVIEW/network-assessment.json"
sha256sum "$EVIDENCE/SHA256SUMS" > "$REVIEW/original-evidence-manifest.sha256"
```

Do not change the original `qualification-summary.md`, which still contains `TO_BE_VERIFIED`, or regenerate its `SHA256SUMS`; preserve both as historically created. Write the corrected observed outcome in a **new review record**. The machine review requires manifest integrity, expected test markers, Pod labels and readiness, policy selector/rules, source script identity and evidence consistency. It **never** approves WP1. Interpret runtime events and review CNI state separately.

## Read-only RBAC and Secret-scope validation

```bash
bash scripts/wp1_rbac_secret_scope.sh 2>&1 | tee "$REVIEW/rbac-secret-scope.log"
```

Required checks: explicitly named kind context; Deployment 1/1; dedicated ServiceAccount; token automount disabled at SA/Pod; UID 10001, non-root, seccomp, read-only rootfs, all capabilities dropped; **no env/envFrom credential references in this particular fixture**; `can-i list secrets` and `can-i create deployments` both `no` for the service account. Do not call `kubectl get secrets -o yaml`, inspect Secret values, or grant additional RBAC merely to make a test pass. If impersonation is not permitted for the operator, log **BLOCKED** and seek authorized review instead of fabricating a denial.

**Secret scope decision:** Application Secret provisioning is `NOT_APPLICABLE` to this credential-free fixture, but managed Secret rotation, revocation, integration with external providers and actual OIDC/JWKS authentication are **NOT_IMPLEMENTED**. An explicitly scoped WP1 local-lab approval may accept that limitation only if the approved acceptance criteria allow it. It does not make the missing enterprise capabilities complete or authorize production.

## Independent reviewer decision record

Reviewer must be a person authorized and independent of the implementation according to project policy. The operator may prepare evidence, but cannot self-certify independence. Review:

1. Original file hashes, source SHA-256, Git working tree, runtime container image digest and tool/CNI versions.
2. Three positive controls and two distinct expected timeouts; compare source/destination IPs and labels. Confirm the CNI and network policy were in effect for the measured paths.
3. Initial transient startup warning versus later receiver readiness and working controls; identify any unexplained warning.
4. The historical bad-image rollout and verified Helm rollback; Pod readiness after probe removal.
5. RBAC negative results, no-token/credential-free fixture contract, and unresolved Secret/OIDC/production scope.
6. Security of evidence handling: **raw `reports/` are local-only**, previous archives contained kubeconfig credentials; sanitize all shared material and address exposed credentials under local policy.

Write the decision into a separate, signed-off record without pretending an independent approval exists:

| Required field | Reviewer to complete |
|---|---|
| Reviewer identity/authority | PENDING |
| Source commit and tested script SHA-256 | PENDING |
| Original evidence SHA-256 manifest digest | PENDING |
| NetworkPolicy differential tests | PASS for tested paths, pending confirmation |
| RBAC and fixture Secret scope | PASS/N/A subject to review |
| Exceptions and open risk register | PENDING |
| WP1 local lab disposition | PENDING / CONDITIONAL / REJECTED / ACCEPTED |
| Signature/approval timestamp | PENDING |
| Production authorization | DENIED |

Only after a real independent decision and completion of the *agreed WP1 lab scope* should `qualification/status.json` change from `in_progress` to `accepted`. This is not permission to override the separate fail-closed production guard. The existing `check_no_production_claims.py` deliberately asserts that **no WP is yet accepted** and requires an intentional, reviewed policy-version change at the first future milestone acceptance.
