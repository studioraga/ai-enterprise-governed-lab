# Source traceability and adapter promotion ledger

## Snapshot and branch inventory

The source archives are user-provided snapshots, *not* live remotes. Exact SHA256 and Git commit IDs are locked in [`../provenance/source-lock.json`](../provenance/source-lock.json).

| Repository / source branch | Capability being evaluated | Planned WP | Acceptance restriction |
|---|---|---|---|
| Platform `main` | `labs/python-api/platform_demo.py` health/double FastAPI, Docker Compose, Helm, offline Terraform | M0/WP1/WP4 | basic demonstration only; no production readiness |
| Platform `research/r03-contract-preparation` | `labs/r03/versioned_contract_lab.py`, OpenAPI compatibility comparison | WP5/WP6 | schema diffs are not deployment verification |
| Platform `feature/r05-extended-sdk-compatibility` | `scripts/qualification/compare_sdk_api.py` and contract suites | WP5/WP6 | external SDK review, owner acceptance required |
| Platform `research/r06-rag-evaluation` | branch currently at `main` commit | WP5 | no independent R06 committed research acceptance |
| Platform `research/r07-governed-agents` | `labs/r07/governed_tool.py` default-deny research; further replay/audit research on branch | WP3/WP5 | not authenticated policy implementation |
| Platform `research/r09-postgresql-rls` | `labs/r09/01_rls_setup.sql`; RLS and tenant-GUC spoofing tests | WP5 | session GUC spoof issue must be fixed before trust claim |
| Platform `research/r10-redis-qdrant` | `labs/r10/idempotent_claim.lua` and tenant-filtering research | WP5 | NX+PX does not mean exactly once |
| Platform `feature/import-principal-v3-baseline` | imported platform engineering baseline | M0 | historical reference only |
| Platform `backup/initial-before-principal-v3-import` | original seed | M0 | historical reference only |
| Governance `main` M0–M29 | `src/`, `governance/`, `scripts/`, `tests/`, `.github/workflows/`; signed research/evidence controls | WP3/WP5/WP6 | independently review scope per module; no wholesale import |
| Governance M30 **uncommitted working tree** | `scripts/m30/`, `schemas/m30/`, `tests/enterprise_freeze/`, `docs/Validation-M30.md` | WP5/WP6 | `freeze_authorized=false`; not a committed release |

The platform archive also contains untracked `labs/r07`, `labs/r09`, `labs/r10`, `tests/r07`, and `docs/engineering` paths. These are NOT automatically equivalent to their branch versions or accepted code.

## Mandatory adapter acceptance record

Every imported adapter must have a dedicated line in this ledger or structured manifest documenting:

1. Source repository, branch and **40-character commit**; if uncommitted, separate patch SHA256 and explicit source-owner disposition.
2. Exact source paths and calculated SHA256; license compatibility; removal of keys, client data and host-specific assumptions.
3. Contract description, dependencies/versions, privileged operations, tenant/identity threat model.
4. Differential tests comparing old research behavior with new adapter, including negative and failure cases.
5. Static/security review, independent engineer approval, acceptance decision, associated target commit.

## Initially identified implementation files (not yet imported)

| Proposed adapter | Origin candidate | First validation |
|---|---|---|
| API contracts | platform R03 / `labs/r03/` | OpenAPI same/compatible/breaking cases |
| SDK boundary | platform R05 / SDK comparator | public API and external consumer tests |
| Policy gate | platform R07 / `labs/r07/governed_tool.py` | forged principal and cross-tenant denial |
| SQL tenancy | platform R09 / `labs/r09/` | protected transaction + GUC spoof test |
| Claim+retrieval | platform R10 / `labs/r10/idempotent_claim.lua` | duplicate claim and tenant result filter |
| Governance verifier | governance M29 + uncommitted M30 scripts/schemas | signature, source chain, missing real-world gate |

Current `feasibility/policy.py` and `feasibility/app.py` are **newly authored demonstration fixtures**; they are not declared as copies or accepted replacements of either source project's controls.
