# Node1 WP1 Helm and Kubernetes Qualification — v3 research instructions

## Scope and important limitations

M0 Compose passed on Node1 on 2026-11-20 (two runs), but the M0 source was untracked in Git at runtime. The v3 chart adds a dedicated tokenless ServiceAccount and an optional NetworkPolicy, while WP1 **is in progress and unaccepted**: initial kind rollout and rollback were verified on Node1; runtime policy enforcement and independent acceptance remain pending. **An installed NetworkPolicy object does not prove enforcement; test runtime traffic on the installed kindnet version.** Kind v0.33 may enforce standard NetworkPolicy using kindnet; run real same-namespace, cross-namespace and egress tests first. Use a separate policy-CNI cluster only if the existing implementation does not enforce. The application still has synthetic JSON-supplied identity and process-only readiness. Do not publish it or treat it as a real tenant boundary.

## Dependencies and sequence

1. Review M0 evidence and source status; run `python3 scripts/verify_m0_compose_record.py` and `bash scripts/verify_baseline.sh`. Confirm the two local reports are intact before committing. Never commit generated reports or credentials.
2. Verify `docker info`, `kubectl version --client`, `helm version`; install a checksum-verified kind binary using the official kind release instructions. Do not assume `kind` is installed.
3. Run `helm lint helm/feasibility` and `helm template feasibility helm/feasibility -n ai-enterprise-feasibility --set image.repository=ai-enterprise-feasibility --set image.tag=local > /tmp/ai-enterprise-wp1.yaml`. Review the ServiceAccount (`automountServiceAccountToken: false`), Deployment (UID, seccomp, probes), Service, NetworkPolicy. A YAML render alone is not enforcement.
4. Stop Compose and local uvicorn to free port 18080. Run `bash scripts/wp1_kind_qualification.sh`. It creates/reuses ONLY `kind-ai-enterprise-feasibility`, loads image and installs Helm chart, then waits for rollout. **This is partial WP1**; do not tag from the helper's result alone.
5. `CTX=kind-ai-enterprise-feasibility; NS=ai-enterprise-feasibility; kubectl --context "$CTX" -n "$NS" get deploy,pod,svc,serviceaccount,networkpolicy -o wide`. `kubectl --context "$CTX" -n "$NS" get events --sort-by=.lastTimestamp`. `helm --kube-context "$CTX" -n "$NS" history feasibility`.
6. `kubectl --context "$CTX" -n "$NS" port-forward svc/feasibility-api 18080:8000` in terminal A; `BASE_URL=http://127.0.0.1:18080 bash scripts/smoke_local.sh` plus `curl -i` for `/readyz` in terminal B. Expected 200 liveness/process readiness, 403 synthetic cross-tenant. Save command exit status and sanitized logs.
7. Check `kubectl --context "$CTX" -n "$NS" get deploy feasibility-api -o yaml` and pod specs; verify token automount disabled, no unnecessary RBAC, non-root UID 10001, drop ALL, read-only rootfs, seccomp. Observe that ServiceAccount alone is **not** OIDC or workload identity.
8. **NetworkPolicy gate:** verify a policy-enforcing CNI is installed. For the installed kindnet version, determine enforcement from controlled positive and negative network tests; until tested, use NOT_VERIFIED. Test permitted in-namespace client connectivity and denied cross-namespace/egress with independently selected test pods. Record CNI, source/destination, timeout and traffic evidence. Reject results from unsupported CNI.
9. **Secret gate:** existing fixture requires no application secret. Document and test the absence of embedded credentials, then implement a Secret/CSI integration contract before claiming enterprise secret handling. Never create dummy secrets in logs as proof of enterprise key management.
10. **Rollback negative drill only on owned disposable kind:** record known-good `helm history` revision and image ID; upgrade to a deliberately missing image tag (non-atomic, with a bounded rollout wait). Capture expected failure, `helm rollback feasibility <KNOWN_GOOD_REVISION> --kube-context "$CTX" -n "$NS"`, recheck 200/200/403, save evidence. Do not paste a literal angle-bracket placeholder into the shell.
11. Record artifacts under ignored `reports/validation/wp1-<UTC timestamp>/`, hash all files, sanitize and obtain independent review. Update README, Architecture, instruction, Milestones, Validation, Runbook and qualification status only after outcomes are observed.
12. Keep WP1 **unaccepted** until negative tests, CNI enforcement, secret-management scope, rollback, evidence and independent reviewer acceptance are satisfied. Then create a separate WP1 commit/tag after manual review.

## Source review warnings

- `image: ...:local` and `IfNotPresent` are fit only for disposable local kind work. For later deployments pin a digest and inspect SBOM/scans.
- `/readyz` currently returns `fixture-ready` without checking external dependencies. It cannot support WP5 availability guarantees.
- A Kubernetes NetworkPolicy object does not guarantee traffic is isolated unless the cluster CNI implements enforcement.
- This chart intentionally does not request additional cluster permissions; the ServiceAccount token is disabled.
- A successful rollback does not imply cluster-level resilience, network isolation, cloud readiness, real OIDC or production authorization.

## Node1 November 21 WP1 checkpoint (local research, not acceptance)

- Initial Helm rendering and kind deployment succeeded; Deployment, Service, ServiceAccount, and NetworkPolicy exist.
- Helm revision 2 was healthy (`ai-enterprise-feasibility:local`); revision 3 was the intentionally missing image; kubelet recorded `ErrImagePull` and `ImagePullBackOff`.
- After the Node1 reboot, Docker/containerd were inactive; existing kind node was recovered without replacement, kubeconfig refreshed, and Kubernetes became reachable.
- Helm revision 4 successfully rolled back to revision 2. Deployment generation 3 was observed, with one updated/ready/available replica and the correct image. Synthetic API checks returned liveness 200, process readiness 200, denied cross-tenant 403, and allowed same-tenant 200.
- The old Pod had one restart after reboot. This was not zero-downtime failover or a test of high availability.
- **NOT ACCEPTED:** NetworkPolicy enforcement has NOT been tested on this specific kindnet cluster (modern kindnet supports the NetworkPolicy API; test actual traffic); no real OIDC, enterprise secrets lifecycle, independently reviewed evidence, or production authorization.
- **Security:** the uploaded test archive included a kubeconfig backup under ignored `reports/validation`; exclude it from every distributed archive, rotate/revoke credentials if disclosure warrants, and do not publish it. Evidence hashing proves integrity only, not secrecy or trust.
- Updated scripts: `scripts/wp1_verify_live_recovery.sh` is a read-only live-state check; `scripts/wp1_capture_safe_evidence.sh` captures a minimal credential-free evidence subset; `scripts/smoke_local.sh` adds positive/negative HTTP checks; the kind helper now blocks ambiguous existing-node recovery.

### Next gate: kind v0.33 NetworkPolicy traffic qualification

**Correction to older runbooks:** Current kindnet versions provide Kubernetes NetworkPolicy enforcement using `kube-network-policies`; do **not** assume kindnet is incapable merely because older documentation said so. Kind v0.33.0 with Kubernetes v1.37.0 should first be tested on the **existing** cluster. The policy object being present is still not a PASS. Record `kubectl --context "$CTX" -n kube-system get ds kindnet -o yaml` and the kindnet container image version. Run `bash scripts/wp1_networkpolicy_probe.sh 2>&1 | tee <safe-local-log>` after reviewing it. It creates one probe Pod in the application namespace and a temporary probe namespace with one client Pod; it does not delete them. The code tests same-namespace ingress HTTP 200, cross-namespace ingress denial, and the selected application Pod's own egress denial by IP (avoids DNS-dependent false results). Verify any denied request was blocked by the policy rather than the client/image being broken; record CNI evidence and contrasting allowed connectivity. Clean up only the explicitly named test Pods/namespace after review. Never claim acceptance from a probe script alone.

## November 21 traffic probe — preliminary results and differential qualification

The first Node1 probe (v5.1) returned exit 0 and observed same-namespace HTTP 200,
other-namespace curl timeout, and an outbound Python socket timeout. This is **initial
behavior evidence**, not independent enforcement acceptance: the original script treated
any nonzero exit as denial and tested an egress connection to the application's own
ClusterIP. Do not record it as a completed NetworkPolicy gate.

Use the revised `scripts/wp1_networkpolicy_probe.sh` on the owned disposable kind
cluster **after manually removing the old probe Pods and namespace**. It uses a
separately labeled, unprotected receiver running the already loaded lab application
image. It requires three positive controls (same-namespace to protected Pod;
same-namespace to control receiver; other-namespace to control receiver) before
requiring a curl timeout for cross-namespace ingress to the protected Pod. It
requires a `socket.timeout` from the protected Pod to the unprotected receiver,
not merely any command failure. It checks the protected Deployment stays ready.
It does not delete test objects automatically, so collect diagnostics and clean up
only its three named probe Pods and one namespace after review. Capture exact
Pod IPs, CNI image, curl and Python exit reasons, and independent-review decision.

These are tests of a **single local cluster**. Passing them would establish
behavioral ingress/egress controls for the tested traffic paths, not comprehensive
NetworkPolicy coverage or authenticated tenant isolation. Secret lifecycle,
additional RBAC controls, trusted identity and independent WP1 approval remain open.


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

## v5.4 independent review checkpoint (2026-11-21)

The v5.3 traffic probe and the two demonstrated RBAC denials passed. Full expected-vs-observed and non-destructive review process: `docs/WP1-Independent-Review.md`. The old v5.3 operator summary contains `TO_BE_VERIFIED` placeholders and is already hashed: never edit it in place. Keep a new assessment in a separate review directory. An early receiver startup-probe warning resolved; record it as a transient observation. WP1 acceptance awaits human authorization and a formally scoped decision; real OIDC and enterprise Secret lifecycle remain unimplemented.
