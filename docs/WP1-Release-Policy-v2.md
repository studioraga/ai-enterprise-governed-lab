# WP1 M0→WP1 lab acceptance — policy v2 (sample)

## Authority boundaries

1. AI may propose only an untrusted action object; it is **never** a grant of permission.
2. `governance_executor.py` checks a fixed allowlist and runs only bounded, read-only checks.
3. `wp1_lab_gate.py` validates frozen contract, pending exception, exact source digest, evidence manifest and optionally an exact-head live GitHub review.
4. `check_no_production_claims.py` validates status **consistency** for M0 or a narrowly approved WP1 LAB state. A forgeable `wp1-approval.json` alone is **not** approval.
5. GitHub protected PR review and an external reviewer must actually approve contract/exception and release policy. CI and branch rules gate the merge.
6. Release custodian makes the reviewed merge/tag decision. Production remains `false`.

## Status transitions

`M0_ACCEPTED_WP1_PENDING` → `CONTRACT_REVIEW_READY` → `EVIDENCE_VERIFIED` → `EXTERNAL_APPROVAL_VERIFIED` → `RELEASE_POLICY_REVIEWED` → `WP1_LAB_CONSISTENT` → `AUTHORIZED_MERGE` → `ANNOTATED_TAG` → `WP2_ENTRY`.

Any missing evidence, stale PR approval, changed commit, unapproved Secret applicability exception or promotion of WP2–WP6 routes to `BLOCKED`. No code in this patch changes the current WP1 state.

## Evidence provenance

- Research commit: `d9c80c264a9b6ce7e4767fed58b009f56b0d91e7`
- Tested probe SHA-256: `3666263ae78d52f41bb7392eeb188d53b54f1d29054fdfb66ebfbd28a229fb68`
- Original manifest digest: `5a779eff4429a056855621b7946d797fdad09719da099c8fffd041b21a23695c`
- Runtime image ID: locally observed, not a source-to-image attestation

The test evidence directory is ignored by Git; an offline CI runner cannot verify it unless supplied with a separately controlled, sanitized artifact. Rehashing evidence is **not** permitted to make a failed check pass.

## Sample CLI

```bash
python3 scripts/check_no_production_claims.py
python3 scripts/wp1_lab_gate.py --root .
python3 scripts/wp1_lab_gate.py --root . --evidence reports/validation/wp1-network-v5.3-20261121T052723Z
printf '%s\n' '{"milestone":"WP1","action":"verify_wp1_contract","requested_release":false}' | python3 scripts/governance_executor.py
```

For an actual PR, require `gh auth status`, a verified PR number, a frozen full head SHA, an independently administered reviewer allowlist, repository branch rules, and use the `--github-pr --repo --base --reviewer --expected-head --evidence` arguments. An offline `READY_FOR_INDEPENDENT_REVIEW` does not authorize merges. Even a `READY_FOR_HUMAN_MERGE_REVIEW` still needs protected PR checks, explicit scope-exception approval and a human decision.

## Gate regression matrix

- Pending M0/WP1 state succeeds.
- Premature WP1 accepted without receipt fails.
- Wrong source/evidence SHA or pending Secret exception fails.
- Production true, WP2 accepted early, self-review fail.
- An internally consistent-looking receipt is **not cryptographically verified** and must be corroborated with live GitHub review and protected branch policy.
- Test historical M0 evidence separately with `--require-evidence` on Node1.

## Release tags

M0 `v0.1.0-m0`; WP1 `v0.2.0-wp1-lab` (scope-delimited variant of proposed `v0.2.0-wp1`); WP2 `v0.3.0-wp2`; WP3 `v0.4.0-wp3`; WP4 `v0.5.0-wp4`; WP5 `v0.6.0-wp5`; WP6 `v0.7.0-wp6`.

The broader suffix-free WP1 tag should not be used for the present synthetic lab without a separately authorized definition.
