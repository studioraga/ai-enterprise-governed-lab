# WP1 deterministic lab acceptance gates (sample framework)

## Trust boundary

AI can draft an action proposal but cannot approve it, provide reviewer identity, mutate acceptance state, or deploy. The `wp1_lab_gate.py` verifier is read-only and fail-closed. The GitHub reviews endpoint is queried live by an authenticated `gh` CLI, with explicitly designated independent approvers. Its result is **readiness for human merge review**, never acceptance, production approval, or an instruction to auto-merge.

## Preflight

```
python3 scripts/wp1_lab_gate.py --root .
python3 scripts/wp1_lab_gate.py --root . --evidence reports/validation/wp1-network-v5.3-20261121T052723Z
```

## Live protected review (after PR opened and independent reviewer approves exact SHA)

```
gh auth status
PR_NUMBER=<actual PR number>
EXPECTED_HEAD=$(git rev-parse origin/review/wp1-lab-acceptance)
python3 scripts/wp1_lab_gate.py --root . \
  --evidence reports/validation/wp1-network-v5.3-20261121T052723Z \
  --repo studioraga/ai-enterprise-governed-lab --github-pr "$PR_NUMBER" \
  --reviewer '<designated-independent-github-login>' \
  --expected-head "$EXPECTED_HEAD"
```

Reviewer allowlist must be taken from independently approved project policy, not an AI suggestion. `gh api` depends on the authentication and authorization available on Node1. A GitHub approval alone is insufficient without branch protection, verified evidence and human authorization. This checker makes **no Git writes** and never performs merge/tag commands.

## Gated transitions

1. Historical M0 PASS; WP1 `in_progress`, production false.
2. Freeze contract and exception as `PENDING` proposals in review PR.
3. Independently verify evidence/source SHA-256, runtime behavior and scope exclusions.
4. Human reviewer approves or rejects N/A application Secret scope.
5. Live GitHub review check requires a designated independent approval on exact current PR head.
6. A separately reviewed release-policy v2 change may permit WP1 `accepted` with an externally verified approval reference.
7. Merge using protected branch review and rerun tests at post-merge SHA.
8. Tag the reviewed lab commit `v0.2.0-wp1-lab` only by authorized release operator.
9. WP2 observability may begin on a new branch after lab entry conditions and documentation are recorded.

Never claim real OIDC/JWKS, managed Secret lifecycle or production readiness. Historic M0 records stay intact. This is a sample framework and does not enforce repository branch rules by itself.
