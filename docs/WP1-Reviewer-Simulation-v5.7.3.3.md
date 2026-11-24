# WP1 reviewer simulation and trust boundary (v5.7.3.3)

- `scripts/wp1_simulate_review.py` uses synthetic fixtures only and does **not** contact GitHub, create a GitHub user, create an approval, write `approved-reviewers.json`, or modify qualification records.
- All simulation output is labeled `SYNTHETIC_TEST_ONLY`, with `trusted_review=false` and `wp1_accepted=false`.
- The live gate requires a genuine independent reviewer appointment, GitHub write permission, actual exact-head review and verified branch protection and required checks.
- The live gate also rejects `enforce_admins.enabled != true`, and rejects a failed check run even when a legacy status with the same context says success.
- The governance owner must attest reviewer independence out of band. A second account controlled by the implementer is not independent.
- Preserve the historical M0 evidence and WP1 in-progress state; never use synthetic output to populate approval receipts or release tags.
