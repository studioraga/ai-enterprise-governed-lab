# Validation matrix, evidence and release gates

## M0 executable validation

```bash
python3 -m venv .venv && . .venv/bin/activate
python -m pip install -e '.[dev]'
bash scripts/preflight.sh
bash scripts/verify_baseline.sh
python3 scripts/verify_project_identity.py
# optional if Docker exists:
bash scripts/diagnose_docker_node1.sh  # only if daemon unavailable
bash scripts/wp0_compose_qualification.sh
# COMPOSE_CLEANUP=1 bash scripts/wp0_compose_qualification.sh
# optional if Helm exists:
helm lint helm/feasibility
helm template feasibility helm/feasibility > /tmp/ai-enterprise-feasibility-rendered.yaml
```

**Verified scope:** M0 unit/API fixture checks, Python compile, provenance schema and fail-closed qualification status. **Not verified in this bundle:** Docker daemon, Helm binary, Kubernetes cluster, OTel, real token verification, cloud access, database query or M30 governance requalification. A `SKIP` is not a PASS. `/readyz` currently reports process-only state.

## Per-milestone verification matrix

| WP | Positive | Must-fail negative | Failure / recovery | Artifacts |
|---|---|---|---|---|
| 1 | image deploy, readiness, API | non-root violation, blocked egress, missing secret | failed rollout, `helm rollback`, app healthy | rendered chart, pods/events, digests, screenshots only if safe |
| 2 | correlated trace + metrics | no PII/token leakage, uninstrumented span alert | collector loss and recovery; auth still deny | OTel trace IDs, PromQL snapshot, redacted logs |
| 3 | valid issuer/audience/key/tenant | forged claim, expired, wrong alg/aud, unknown kid | JWKS rotation, IdP outage | JWT test vectors (fake), verifier logs |
| 4 | approved private deployment | forbidden public access, over-permission | outage and clean destroy | Terraform plan digest, IAM review, audit, cost/teardown |
| 5 | approved same-tenant action, provenance | cross-tenant CRUD, GUC spoof, replay, tamper | DB/Redis/Qdrant crash; safe retry/rollback | policy/SQL tests, immutable verifier report |
| 6 | CI build/test/promote | bad scan, missing signature, bypass attempt | bad image, redeploy + rollback | job logs, SBOM, SLSA-style provenance, approval |

## Required verifier output model

Each milestone records: schema version, git commit, branch, source manifest hashes, environment and dependency versions, test commands, timestamps, tool exit codes, success/failure counts, negative results, `NOT_RUN` entries, unresolved issues, reviewer and acceptance decision. Do not commit credentials or real PII.

**Gate precedence:** `source verified` -> `design approved` -> `tests pass` -> `negative cases pass` -> `independent evidence complete` -> `manual acceptance`. A later green status cannot override an earlier red gate; evidence integrity cannot override insecure actual environment conditions.

## M30 governance specific

The uploaded M30 `m30-production-freeze-decision.json` says `freeze_authorized: false`; it must remain independent of this demo's success. New integration verification can generate its own decision document, but it cannot mutate, re-sign or supersede M30 without an authorized governance process. No regulatory/certification claim is made.


## November 20 v3 checkpoint

M0 Docker Compose qualification: **locally verified** using two Node1 runs and evidence checksum revalidation. `qualification/m0-compose-local.json` records the scope and provenance limits. WP1 now **IN_PROGRESS/UNACCEPTED** (initial kind rollout and rollback verified; NetworkPolicy and independent approval pending). Refer to `docs/WP1-Node1-Qualification.md` for dependency, manifest, rollback, CNI enforcement, security and evidence gates. Production remains denied.

## Node1 November 21 WP1 checkpoint (local research, not acceptance)

- Initial Helm rendering and kind deployment succeeded; Deployment, Service, ServiceAccount, and NetworkPolicy exist.
- Helm revision 2 was healthy (`ai-enterprise-feasibility:local`); revision 3 was the intentionally missing image; kubelet recorded `ErrImagePull` and `ImagePullBackOff`.
- After the Node1 reboot, Docker/containerd were inactive; existing kind node was recovered without replacement, kubeconfig refreshed, and Kubernetes became reachable.
- Helm revision 4 successfully rolled back to revision 2. Deployment generation 3 was observed, with one updated/ready/available replica and the correct image. Synthetic API checks returned liveness 200, process readiness 200, denied cross-tenant 403, and allowed same-tenant 200.
- The old Pod had one restart after reboot. This was not zero-downtime failover or a test of high availability.
- **NOT ACCEPTED:** NetworkPolicy enforcement has NOT been tested on this specific kindnet cluster (modern kindnet supports the NetworkPolicy API; test actual traffic); no real OIDC, enterprise secrets lifecycle, independently reviewed evidence, or production authorization.
- **Security:** the uploaded test archive included a kubeconfig backup under ignored `reports/validation`; exclude it from every distributed archive, rotate/revoke credentials if disclosure warrants, and do not publish it. Evidence hashing proves integrity only, not secrecy or trust.
- Updated scripts: `scripts/wp1_verify_live_recovery.sh` is a read-only live-state check; `scripts/wp1_capture_safe_evidence.sh` captures a minimal credential-free evidence subset; `scripts/smoke_local.sh` adds positive/negative HTTP checks; the kind helper now blocks ambiguous existing-node recovery.

## WP1 NetworkPolicy differential-test correction (November 21)

The original probe returned 0 with HTTP 200 for same-namespace ingress and network
timeouts for cross-namespace ingress / selected-Pod egress. Preserve that output as
preliminary evidence only; `kubectl exec` nonzero may reflect reasons other than policy.
The updated probe checks an unprotected same-namespace receiver from both source
namespaces and demands specific timeout results for the protected Pod. Use exact
`kind-ai-enterprise-feasibility` context and preserve the probe output, kindnet
version/logs, source/destination Pod IPs, `kubectl describe` output and SHA256SUMS.
Do not modify production release status or accept WP1 automatically.


## WP1 v5.3 receiver-readiness correction (2026-11-21)

The Node1 v5.2 differential probe started all three disposable Pods but failed
on the *same-namespace to unprotected receiver* positive control with
`curl: (7) Failed to connect to <receiver-pod-ip>:8000` (exit 7).
This is **not proof of NetworkPolicy denial**: the receiver was created with
`kubectl run` without a readinessProbe, so Pod Ready did not guarantee Uvicorn
had bound port 8000. Inspect the retained receiver logs and local HTTP response
before attributing the failure to startup timing; a command/entrypoint error
remains possible until diagnosed.

The corrected probe creates a labeled receiver Pod with startup and HTTP readiness
probes, non-root identity, no service-account token, a read-only root filesystem
and restricted capabilities. It also verifies receiver-loopback HTTP 200 before
proceeding to three positive cross-Pod controls and two expected timeout denials.
If loopback is unavailable, the test is BLOCKED, not a policy failure or PASS.
Preserve the failed probe's evidence and inspect ownership before manually
deleting exactly the test Pods and test namespace. Do not delete the application,
Helm release or kind cluster. Re-run once and record CNI details, Pod IPs,
control successes, denial error types and SHA-256 evidence before review.
WP1 remains IN_PROGRESS; production authorization stays denied.

## WP1 v5.4 source and evidence gate

Preserve original SHA256SUMS of the v5.3 differential report. `python3 scripts/wp1_review_network_evidence.py --evidence <directory> --source scripts/wp1_networkpolicy_probe.sh` confirms file integrity, source identity, three positive controls, two timeout markers, policy selector, and receiver readiness. The result is `PASS_PENDING_HUMAN_REVIEW`, **never automatic acceptance**. `bash scripts/wp1_rbac_secret_scope.sh` verifies denied workload RBAC and no-credential fixture scope using read-only calls. A transient receiver startup warning was observed and subsequently recovered. See `docs/WP1-Independent-Review.md`.
