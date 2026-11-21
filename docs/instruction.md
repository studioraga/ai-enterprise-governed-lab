# Engineering instruction and step-by-step implementation procedure

## Mandatory procedure for every milestone

1. Review original `provenance/source-lock.json` and relevant **actual branch** source (not only `main`), inspect README and latest failure logs. Treat source archives as untrusted; no direct executables or scripts from them run in new CI before audit.
2. Write/update `docs/Architecture.md`, `docs/Milestones.md`, `docs/Validation.md`, `docs/Source-Traceability.md`, security model, and affected ADRs **before implementation**. Design review gate DR-n requires manual acknowledgment.
3. Implement the smallest integration slice on `feature/wpN-...` in the new repository; do **not** merge or tag upstream source. Record source commit and verified extraction in the adapter ledger.
4. Run positive, negative, malformed-input, failure recovery, performance and rollback tests. Capture commands, environment, timestamps, versions, return codes, sanitized logs, digest manifest and independent reviewer disposition.
5. Update docs and produce one milestone-specific evidence summary. Merge to the new repository's `main` only after review. Push/tag only after manual approval. A tag records *research milestone acceptance*, not production authorization.

For the verified repository rename, Node1 environment configuration, safe Git handling, image build, Helm qualification and controlled rollback commands, see [Node1-Setup.md](Node1-Setup.md). The uploaded project already has an initialized `.git` and an existing `origin`; do not reinitialize it.

## M0 — Baseline present in this bundle

**Dependencies:** Ubuntu 24.04 or equivalent, Python >=3.10, Git. Optional `docker`, `helm`, `kubectl`, `kind`, `terraform`, AWS/Azure CLIs. No network service or cloud account required for pure Python tests.

```bash
python3 -m venv .venv && source .venv/bin/activate
python -m pip install -e '.[dev]'
bash scripts/preflight.sh
bash scripts/verify_baseline.sh
# Docker daemon must be running before continuing to Step 5:
bash scripts/wp0_compose_qualification.sh
```

Expected: 10 fixture tests pass; schema and deny-by-default release status pass. Tool-dependent checks are **skipped** if tools are absent, never marked PASS. The synthetic identity API is not an authentication system. M0 is not eligible for production.

## WP1 — Kubernetes integration (M1)

**Depends:** M0 source lock and explicit `DR-1` review.

1. Freeze image runtime and dependency versions, generate SBOM, scan dependencies, build as UID 10001. Confirm multi-arch requirements for x86_64 Node1 versus arm64 Jetson.
2. Install Docker Engine and kind/k3s on an **approved lab**; check host CPU/RAM, kube-context, DNS, CNI, kernel, cgroup2, container runtime. Document version output and cleanup.
3. Validate chart with `helm lint` and `helm template`; implement namespace-specific ServiceAccount, Secret references, PodSecurity restricted settings, quotas, requests/limits, disruption behavior, NetworkPolicy and ingress TLS termination.
4. `bash scripts/wp1_kind_qualification.sh` starts the example rollout only; then run `kubectl describe`, deployment logs, a host-side port-forward, readiness/liveness adversarial drills, non-root and NetworkPolicy denial checks.
5. Perform controlled bad-image upgrade; show rollout failure, `helm rollback` to known digest and restored health. Destroy test cluster after preserving sanitized evidence.
6. Mark WP1 accepted only after cluster runtime logs, signed operator verification, secrets/NetworkPolicy checks and rollback meet `docs/Validation.md`.

**Do not expose the synthetic M0 governed endpoint outside localhost.** Before real traffic, WP3 identity checks are prerequisite.

## WP2 — Observability (M2)

**Depends:** deployed lab WP1; explicit DR-2.

1. Add OpenTelemetry Python SDK instrumentation to incoming API requests and outbound policy/database/tool spans; do not record prompt, PII, tokens, credentials or unrestricted database queries.
2. Deploy Collector with OTLP receiver, memory limiter, batch processor and bounded exporter; add Prometheus scraping and Grafana dashboards.
3. Define service SLIs: request availability, p95 latency, error classes, policy-denial counts, dependency timeout counts, tool completion; document target SLOs after measured baseline, not invented thresholds.
4. Generate synthetic request with known trace ID; correlate API -> policy -> datastore/tool and logs. Redact and sample correctly.
5. Inject dependency outage / timeout, show matching alerts, incident response, resolution and evidence capture. Fail-open authorization is forbidden during telemetry failure.

## WP3 — Enterprise identity (M3)

**Depends:** WP2 plus threat review; DR-3; trusted isolated IdP (e.g., local Keycloak) for lab first.

1. Define OIDC issuer, allowed signing algorithms, audience(s), tenant entitlement claim, scope and key rotation contract. Reject token-controlled tenant override by mapping resource ownership server-side.
2. Validate JWT signature against HTTPS-pinned/approved JWKS with bounded cache, `kid` selection, revocation/key-rollover policy, clock tolerance, `exp`, `nbf`, `iss`, `aud`, and algorithm confusion tests.
3. Enforce tenant binding in API and downstream database/tool calls; never authorize from caller's JSON field.
4. Run missing/expired/invalid-signature/wrong-issuer/wrong-audience/other-tenant/unknown-key/outage tests and authenticated same-tenant success.
5. Preserve redacted evidence; refuse promotion if live auth control is bypassed or simulator is still on the trusted route.

## WP4 — Controlled cloud deployment (M4)

**Depends:** WP3 authenticated endpoint and network review; DR-4 and explicit account/cost approval.

1. Choose ONE provider (AWS or Azure) for the first real qualification. Document account/subscription, region, cost budget, ownership, allowable public endpoints, required tags, and teardown plan; do not embed credentials.
2. Use Terraform modules with pinned providers/state backend, encryption, state locking, IAM least privilege, private networking, security groups/NSG, external secrets vault, logging and resource ownership.
3. Separate `fmt`, `validate`, `plan`, independent plan review, manual `apply`, smoke/security checks, immutable digest, approval-based `destroy`; prevent automatic apply on pull requests.
4. Collect plan digest, policy results, ingress/egress denial, identity and secret retrieval, availability and monthly estimated spend.
5. Run explicit teardown and zero-orphan verification; missing teardown is a hard blocker.

## WP5 — R07/R09/R10/M30 integration (M5)

**Depends:** WP3 identity and WP1/2 operational evidence. Cloud is optional for the local integration test, but required for cloud production promotion. DR-5 must explicitly approve each source adapter.

1. Import **interfaces selectively** from R07, R09, R10 research and M29/M30 control manifests. Record code provenance, upstream license, commit, hash, review and sanitization; keep source repositories unchanged.
2. Build deterministic trust boundary: verified principal -> action allow-list -> ownership -> scoped approval -> bounded executor -> audited result. Add replay, deadlines and cancellation postchecks, test no side effects on denial.
3. Implement PostgreSQL RLS with a tenant binding that is resistant to R09 custom-GUC spoofing; test malicious `SET`, connection pool reuse, all CRUD, transaction rollback and bypass roles.
4. Implement Redis claim ownership/completion/recovery state machine; do not promise exactly-once effects. Implement tenant-filtered Qdrant retrieval and cross-tenant post-filter rejection; include compromised-filter test.
5. Add M30-style *independent evidence verifier* and candidate manifest. Fail closed when source signatures, independent receipt, secure boot/MAC, authorized pentest, organizational/BCP or other mandatory release evidence is missing.
6. Keep upstream `freeze_authorized=false` and current candidate status unchanged. Any future production decision requires new independent authorization for this target, not reinterpretation of M30's existing signed decision.

## WP6 — CI/CD qualification and final interview demo (M6)

**Depends:** WP1–WP5 accepted in scope and DR-6.

1. GitHub Actions: format/lint, dependency lock checks, pytest, API backward compatibility, SAST/secrets/SBOM, container digest, image scan, IaC policy, synthetic negative tests.
2. Establish immutable artifact promotion between local -> staged -> approved cloud; use environments and mandatory human reviewer; no unattended production deploy.
3. Inject failures: identity outage, JWKS unknown key, policy denial, tenant access, Redis crash, Qdrant filter failure, OTel outage, bad image, rollback and evidence mismatch.
4. Verify archived source hashes, deterministic test outputs, logs, reviewer attestations and distinct status for design/prototype/validated/accepted/production-authorized.
5. Demo: feasibility yes/no in client stack, troubleshooting timeline, safe deployment, governance, rollback and reusable integration playbook.

## Qualification and source import checklist

For every WP, update the manifest: branch name, commit, source, license, reviewer, dependency lock, test vector counts, SHA256 checks, failures, recovery evidence, and acceptance gate. Require a human signature or explicit documented approval before a release tag. No release if essential tools were skipped.


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

## WP1 v5.4 review continuation

After v5.3 probe completion, do **not** rerun the fault injection. The original differential bundle remains immutable. Create a new review directory, run `python3 scripts/wp1_review_network_evidence.py --evidence reports/validation/wp1-network-v5.3-20261121T052723Z --source scripts/wp1_networkpolicy_probe.sh --output reports/validation/wp1-review-<STAMP>/network-assessment.json`, then run `bash scripts/wp1_rbac_secret_scope.sh`. Follow `docs/WP1-Independent-Review.md` for human signoff. WP1 and production remain unaccepted.
