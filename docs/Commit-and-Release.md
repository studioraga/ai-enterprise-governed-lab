# Git, commit, evidence and release procedure — renamed project

## Current uploaded Git state

The uploaded `ai-enterprise-governed-lab` archive **already contains `.git`**, an initial `main` commit (`819915f`), and an `origin` set to `https://github.com/studioraga/ai-enterprise-governed-lab.git`. Its M0 source files were untracked at upload. **Do not `git init`, replace `.git`, or add a duplicate `origin`.** The original history is authoritative. The project rename has changed source identifiers and internal schema strings; upstream archive hashes in source provenance remain unchanged.

Check the actual Node1 state first:

```bash
cd ~/dev/pub/ai-enterprise/ai-enterprise-governed-lab
git status --short --branch
git log --oneline --decorate -5
git remote -v
git tag -l
bash scripts/verify_baseline.sh
```

Follow [Node1-Setup.md](Node1-Setup.md) for safe archive application, staged review, environment verification, and exact commit/push commands. Do **not** paste the old `git init -b main`/`git remote add origin` procedure into this existing repository.

## Proposed M0 commit subject

`feat(baseline): establish renamed AI enterprise governed lab M0`

Detailed message:

```text
Why:
- Establish a vendor-neutral, independent reference engineering lab for feasibility and governed AI integration.
- Align all image, kind, namespace, provenance, qualification and workflow names.

Changes:
- Review and preserve existing Git metadata; retain source-lock upstream commit and hash provenance.
- Add source identity validation and fail-closed qualification checks.
- Protect Docker build context and use explicit kind Kubernetes context.
- Document Node1 installation, smoke checks, optional cluster exercise and rollback.

Validation:
- Python unit/negative tests, source-lock validation, rename scan, production deny guard.
- Docker/Helm/Kubernetes steps are NOT_RUN unless logs prove their execution.

Restrictions:
- M0-only; no inherited M30 production approval; WP1–WP6 remain planned.
- No upstream source merges and no unreviewed cloud or GitHub push.
```

## Proposed feature branches and milestone tags

| Milestone | Branch | Example commit subject | Tag after independent acceptance |
|---|---|---|---|
| M0 | main | `feat(baseline): establish renamed AI enterprise governed lab M0` | `v0.1.0-m0` |
| WP1 | `feature/wp1-kubernetes` | `feat(k8s): qualify hardened local Helm deployment and rollback` | `v0.2.0-wp1` |
| WP2 | `feature/wp2-observability` | `feat(observability): correlate API policy data and tool spans` | `v0.3.0-wp2` |
| WP3 | `feature/wp3-oidc` | `feat(identity): enforce OIDC JWKS and trusted tenant binding` | `v0.4.0-wp3` |
| WP4 | `feature/wp4-cloud` | `feat(cloud): qualify approved private deployment and teardown` | `v0.5.0-wp4` |
| WP5 | `feature/wp5-governed-data` | `feat(governance): integrate reviewed R07 R09 R10 and evidence gates` | `v0.6.0-wp5` |
| WP6 | `feature/wp6-cicd` | `ci(qualification): gate supply chain promotion and rollback` | `v0.7.0-wp6` |

## Commit/review/merge rules

Before each feature commit: update architecture and dependency contracts, run positive/negative tests, capture tool versions and redacted logs, record upstream source branch and file digests, and run `git diff --cached --check`. Merge a feature branch to `main` via review only after documented acceptance. Tag the **reviewed main commit**, not an unreviewed worktree. No new tag authorizes enterprise production by implication. Maintain the inherited governance M30 freeze status independently.

## Stop conditions

- Missing or failed negative tests, unresolved supply-chain issues, secrets in staged files, source provenance mismatches, or unreviewed license dependencies.
- Skipped runtime validation is reported `NOT_RUN`, never counted `PASS`.
- Do not force-push, alter upstream tags, add live secrets, or claim production authorization from a signed test fixture.


## November 20 v3 checkpoint

M0 Docker Compose qualification: **locally verified** using two Node1 runs and evidence checksum revalidation. `qualification/m0-compose-local.json` records the scope and provenance limits. WP1 still **NOT_RUN/UNACCEPTED**. Refer to `docs/WP1-Node1-Qualification.md` for dependency, manifest, rollback, CNI enforcement, security and evidence gates. Production remains denied.
