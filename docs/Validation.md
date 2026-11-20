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

M0 Docker Compose qualification: **locally verified** using two Node1 runs and evidence checksum revalidation. `qualification/m0-compose-local.json` records the scope and provenance limits. WP1 still **NOT_RUN/UNACCEPTED**. Refer to `docs/WP1-Node1-Qualification.md` for dependency, manifest, rollback, CNI enforcement, security and evidence gates. Production remains denied.
