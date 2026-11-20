# Node1 WP1 Helm and Kubernetes Qualification — v3 research instructions

## Scope and important limitations

M0 Compose passed on Node1 on 2026-11-20 (two runs), but the M0 source was untracked in Git at runtime. The v3 chart adds a dedicated tokenless ServiceAccount and an optional NetworkPolicy, while WP1 **remains NOT_RUN** pending actual kind rollout and independent acceptance. **kind's default network implementation does not prove NetworkPolicy enforcement.** A separate policy-enforcing CNI must be qualified before claiming an isolation PASS. The application still has synthetic JSON-supplied identity and process-only readiness. Do not publish it or treat it as a real tenant boundary.

## Dependencies and sequence

1. Review M0 evidence and source status; run `python3 scripts/verify_m0_compose_record.py` and `bash scripts/verify_baseline.sh`. Confirm the two local reports are intact before committing. Never commit generated reports or credentials.
2. Verify `docker info`, `kubectl version --client`, `helm version`; install a checksum-verified kind binary using the official kind release instructions. Do not assume `kind` is installed.
3. Run `helm lint helm/feasibility` and `helm template feasibility helm/feasibility -n ai-enterprise-feasibility --set image.repository=ai-enterprise-feasibility --set image.tag=local > /tmp/ai-enterprise-wp1.yaml`. Review the ServiceAccount (`automountServiceAccountToken: false`), Deployment (UID, seccomp, probes), Service, NetworkPolicy. A YAML render alone is not enforcement.
4. Stop Compose and local uvicorn to free port 18080. Run `bash scripts/wp1_kind_qualification.sh`. It creates/reuses ONLY `kind-ai-enterprise-feasibility`, loads image and installs Helm chart, then waits for rollout. **This is partial WP1**; do not tag from the helper's result alone.
5. `CTX=kind-ai-enterprise-feasibility; NS=ai-enterprise-feasibility; kubectl --context "$CTX" -n "$NS" get deploy,pod,svc,serviceaccount,networkpolicy -o wide`. `kubectl --context "$CTX" -n "$NS" get events --sort-by=.lastTimestamp`. `helm --kube-context "$CTX" -n "$NS" history feasibility`.
6. `kubectl --context "$CTX" -n "$NS" port-forward svc/feasibility-api 18080:8000` in terminal A; `BASE_URL=http://127.0.0.1:18080 bash scripts/smoke_local.sh` plus `curl -i` for `/readyz` in terminal B. Expected 200 liveness/process readiness, 403 synthetic cross-tenant. Save command exit status and sanitized logs.
7. Check `kubectl --context "$CTX" -n "$NS" get deploy feasibility-api -o yaml` and pod specs; verify token automount disabled, no unnecessary RBAC, non-root UID 10001, drop ALL, read-only rootfs, seccomp. Observe that ServiceAccount alone is **not** OIDC or workload identity.
8. **NetworkPolicy gate:** verify a policy-enforcing CNI is installed. If using default kindnet, set enforcement status BLOCKED/NOT_RUN. Test permitted in-namespace client connectivity and denied cross-namespace/egress with independently selected test pods. Record CNI, source/destination, timeout and traffic evidence. Reject results from unsupported CNI.
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
