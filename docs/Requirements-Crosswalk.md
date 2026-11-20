# Requirements inheritance and acceptance crosswalk

This file specifies **traceability**, not a claim that every legacy requirement is implemented in the new baseline. The 2 source snapshots are evidence and design inputs; no full-source merge is authorized. Any requirement inherited in future must have its own requirement ID, source commit, implementation path, negative test and reviewer disposition.

## Platform baseline R01–R16, mapped to integration milestones

The source `docs/roadmap.md` explicitly identifies these requirements and **does not treat R01–R16 as accepted**. The work below maps each to new-project deliverables.

| Platform requirement | Original focus per roadmap | New project milestone | Current new-project status |
|---|---|---|---|
| R01 | Architecture / ADRs | M0 + all stages | Design only |
| R02 | Python/React reliability and edge cases | M0, M6 | Minimal Python fixture tests only |
| R03 | Versioned OpenAPI contracts, clients and breaking changes | M5, M6 | Upstream branch identified; not migrated |
| R04 | Python/React performance and edge cases | M2, M6 | Planned |
| R05 | SDK methods, exports, types, serialization, errors and approval boundaries | M5, M6 | Upstream research identified; not migrated |
| R06 | Retrieval quality / evaluation | M5 | Not independently committed on R06 branch |
| R07 | Bounded agents, policy approval/denial and audit | M3, M5 | Local policy demonstration only; not source adapter |
| R08 | Cloud portability (source docs) | M4 | Planned; offline Terraform not cloud qualification |
| R09 | PostgreSQL RLS, identity, concurrency, EXPLAIN and negative tests | M5 | Upstream research identified; spoofing issue open |
| R10 | Redis idempotency/replay + tenant-scoped Qdrant retrieval | M5 | Upstream research identified; not integrated |
| R11 | OIDC/JWT/JWKS negatives | M3 | Planned |
| R12 | OpenTelemetry / SLI / SLO incidents | M2 | Planned |
| R13 | CI signing, reproducibility and provenance | M6 | Minimal M0 GitHub CI fixture only |
| R14 | Architecture and principal-level evidence | M6 | Design/interview documentation started |
| R15 | Measured AI coding / role evidence | M6 | Planned |
| R16 | Executive architecture / delivery evidence | M6 | Planned |

**Note:** R08 and R14–R16 labels are drawn from the available project roadmap grouping, not independently accepted requirement specifications. Before importing them, open the exact underlying requirement artifact and replace the grouping with source-accurate acceptance identifiers.

## Governance M0–M30 intake mapping

These are **intake domains**, not a transfer of signoff, certification or code ownership. Inspect the source `docs/Validation-M*.md`, `docs/Deployment-M*.md`, `schemas/m*`, `scripts/m*` and test packages at each import milestone before selecting adapters.

| Governance domain | Source milestones | New milestone / dependency | Gate |
|---|---|---|---|
| Trust kernel, deterministic authorization, bounded agents, approved side effects | M0–M10 | M3/M5 | verified identity, authorization, no side effect on deny |
| Product security / CRA research, vulnerability processes, signing and evidence workflows | M11–M20 | M5/M6 | signed evidence and independent applicability review |
| Embedded Linux platform hardening, trusted compute, secure boot and MAC controls | M21–M22 | M4/M5 | real platform evidence before release |
| Enterprise identity, MFA, PAM, data/crypto security, zero-trust networking | M23–M25 | M1/M3/M4/M5 | OIDC and secret tests; isolation and negative networking |
| Incident response, operational recovery and secure development controls | M26–M28 | M2/M6 | operational incident tests, authorized pentest, organizational evidence |
| Independent Node1/Node2 cross-domain verification | M29 | M5/M6 | independent receipt, provenance, applicable host trust |
| Enterprise security evidence and production-freeze decision | M30 **uncommitted** | M5/M6 | production freeze denies until all real controls reviewed |

Do not import all 30 milestone source directories or their private evidence into a public repository. The new project's M0–M6 system follows **selective adapters** with explicit source path, license/security review, contract and tests, and blocks absent requirements rather than marking them completed.

## Target demonstration acceptance by AI Enterprise Labs role requirement

| Interview requirement | Planned proof | Work packages |
|---|---|---|
| Learn unfamiliar client stacks / fast feasibility | source inventory, constraints, go/no-go feasibility report | M0, WP1, WP4 |
| Deep debugging / deployment failures | injected network/API/data/cluster failures with traces | WP1, WP2, WP5 |
| Real APIs, agents, RAG and SQL | versioned contracts, trusted agent/tool/data adapters | WP3, WP5 |
| Security, PII and governance | policy denies, tenant isolation, independent frozen evidence | WP3, WP5, WP6 |
| Docker/Kubernetes/CI | real workload, lifecycle, protected promotion | WP1, WP6 |
| AWS/Azure practical integration | approved private target, identity, secrets, teardown | WP4 |
| Reusable Factory IP | documented module, ADR, runbook, test vectors and no customer secrets | every WP |
