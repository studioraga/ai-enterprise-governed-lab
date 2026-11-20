# Milestones and dependency contracts

| Milestone | Branch proposal | Tag proposal (do not create prematurely) | Prerequisite | Required acceptance evidence |
|---|---|---|---|---|
| M0 baseline | `feature/m0-import-and-design` | `v0.1.0-m0` | Two snapshot hashes, DR-0 | docs, source lock, local fixture tests, reviewers |
| M1 Kubernetes | `feature/wp1-kubernetes` | `v0.2.0-wp1` | M0, DR-1 | live cluster rollout, denial, rollback, chart, logs |
| M2 observability | `feature/wp2-observability` | `v0.3.0-wp2` | M1, DR-2 | trace/metric/log correlation and incident drill |
| M3 identity | `feature/wp3-oidc` | `v0.4.0-wp3` | M2, DR-3 | real JWKS, key rollover, forged tenant denials |
| M4 cloud | `feature/wp4-cloud` | `v0.5.0-wp4` | M3, DR-4 | provider review, IAM, network, plan/apply/destroy |
| M5 governed data | `feature/wp5-governed-data` | `v0.6.0-wp5` | M3/M4, DR-5 | R07/R09/R10/M30 adapter qualification |
| M6 release pipeline | `feature/wp6-cicd` | `v0.7.0-wp6` | M1–M5, DR-6 | independent gated pipeline, canary, rollback |

All tags identify **accepted lab milestones only**. Production authorization is independent and remains denied until a separate release board and evidence gate pass.

## Proposed new-repository Git development graph

```mermaid
gitGraph
  commit id: "M0-design"
  branch feature-wp1
  checkout feature-wp1
  commit id: "M1-k8s"
  checkout main
  merge feature-wp1
  branch feature-wp2
  checkout feature-wp2
  commit id: "M2-otel"
  checkout main
  merge feature-wp2
  branch feature-wp3
  checkout feature-wp3
  commit id: "M3-oidc"
  checkout main
  merge feature-wp3
  branch feature-wp4
  checkout feature-wp4
  commit id: "M4-cloud"
  checkout main
  merge feature-wp4
  branch feature-wp5
  checkout feature-wp5
  commit id: "M5-governed-data"
  checkout main
  merge feature-wp5
  branch feature-wp6
  checkout feature-wp6
  commit id: "M6-ci-qualification"
  checkout main
  merge feature-wp6
```

*The graph is a future plan, not a representation of commits that have already occurred.* Preserving original research history means keep source project branches and tags completely unchanged. The new repo starts independently with provenance pointers.

## Acceptance state machine

```mermaid
stateDiagram-v2
  [*] --> Planned
  Planned --> DesignReviewed: DR approval
  DesignReviewed --> Implemented: source and configuration
  Implemented --> Tested: positive/negative checks
  Tested --> IndependentlyReviewed: verifier + evidence
  IndependentlyReviewed --> AcceptedLab: all gate obligations passed
  IndependentlyReviewed --> Blocked: mismatch or missing evidence
  Blocked --> Implemented: corrective patch
  AcceptedLab --> ProductionCandidate: separate scoped assessment
  ProductionCandidate --> ProductionAuthorized: external approval + complete controls
  ProductionCandidate --> Blocked: any missing control
```

## Implementation acceptance discipline

- Every report must state `PASS`, `FAIL`, `BLOCKED`, or `NOT_RUN`, not silently treat missing dependencies as success.
- A source branch head, an untracked file and a signed evidence artifact are not interchangeable.
- Require negative cases: wrong-tenant, unauthorized tool, forged JWKS, revoked approval, unavailable dependency, interrupted rollback and tampered evidence.
- Maintain milestone-specific `reports/validation/<timestamp>/` outside Git by default; publish only sanitized manifest summaries after review.


## November 20 v3 checkpoint

M0 Docker Compose qualification: **locally verified** using two Node1 runs and evidence checksum revalidation. `qualification/m0-compose-local.json` records the scope and provenance limits. WP1 still **NOT_RUN/UNACCEPTED**. Refer to `docs/WP1-Node1-Qualification.md` for dependency, manifest, rollback, CNI enforcement, security and evidence gates. Production remains denied.
