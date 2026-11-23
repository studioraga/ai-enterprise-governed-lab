# WP1 v5.7.3 — review request and protected-release gate

## Baseline

- Original v5.7.2 PR #2: open, frozen head `de44815...`; **do not assume approved**.
- Node1 `gh pr checks --required --json` fails because its CLI lacks `--json`.
- Node1 `gh pr edit --add-reviewer` hits deprecated Projects (classic) `projectCards` GraphQL lookup.
- GitHub reported **zero applicable rules** for both the WP1 feature branch and main.
- Current synthetic fixture: WP1 `in_progress`; production `false`. The Secret exception is `PENDING`.

## Corrections

`wp1_request_review.py` uses `POST /repos/{owner}/{repo}/pulls/{pr}/requested_reviewers`, not `gh pr edit`.

`wp1_live_release_gate.py` uses GitHub REST endpoints:

1. `GET .../pulls/{pr}` — exact head, base, open/draft/mergeability
2. `GET .../pulls/{pr}/reviews?per_page=100` — review history via `gh api --paginate` (no `--slurp`)
3. `GET .../branches/{base}/protection` — effective classic branch protection; no protection => BLOCKED
4. `GET .../commits/{head}/check-runs?per_page=100` — required check-run conclusions
5. `GET .../commits/{head}/status` — legacy commit status contexts

The verifier requires at least one independent eligible reviewer, an exact-head approval, configured required pull request review(s), stale-review dismissal or last-push approval, required `governance-source`, and all required checks green. It explicitly denies force-pushable or deletable target branches. Failure fetching branch protection fails closed; **ruleset-only environments need a separately audited ruleset backend**, not bypassing this gate.

The current user-controlled `approved-reviewers.json` is a sample input, NOT itself a trusted independent authority. A separately administered policy, verified team membership, or protected CODEOWNERS/branch rule must establish eligibility. Do not auto-create eligibility based on PR author, AI output, a blank file, or arbitrary GitHub accounts.

## Explicitly not automated

- Creating reviewer approval
- Fabricating a Secret exception disposition
- Altering branch protection or bypassing required checks
- Merging, setting WP1 accepted, tagging or authorizing production

## CI limitation

`wp1-governance.yml` verifies source only; it does not import independently controlled Node1 evidence. WP1 promotion additionally requires a verified private evidence record and a protected external approval. The current gate expects **classic branch protection REST** because it is conservative and easier to audit. For repository rulesets, extend verification of `GET /repos/{owner}/{repo}/rules/branches/{branch}` plus rule parameters with tests before treating those as authoritative.

## Procedure

1. On the clean release-authorization review worktree, apply this source-only patch.
2. Run `python3 -m pytest -q tests` and `bash scripts/verify_baseline.sh`.
3. Confirm PR #2 is open and its frozen full SHA still matches.
4. Obtain an independently administered reviewer policy; a blank `.json` is a BLOCKED state.
5. Use `python3 scripts/wp1_request_review.py --repo "$REPO" --pr "$PR_NUMBER" --reviewers-file "$REVIEWER_POLICY"` to request, not grant, review.
6. Have authorized repository administration enable reviewed branch protection with required review and required `governance-source` check, without admin bypass.
7. Only after an independently submitted approval and successful required checks, run `wp1_live_release_gate.py` against the frozen PR SHA.
8. If `READY_FOR_AUTHORIZED_MERGE`, a separately authorized custodian may request a normal protected merge. Verify state becomes MERGED before starting a separate WP1 milestone promotion PR.
9. Keep contract/exception pending until real approval, and never publish WP1 lab tag until accepted and released via main.
