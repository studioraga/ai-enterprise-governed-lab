# WP1 v5.7.2 — GitHub CLI compatibility and review sequence

## Verified issue

Node1 `gh api` does not support `--slurp`; earlier historical and live PR-review verifiers used this unsupported flag. Both now invoke `gh api --paginate` and parse one or multiple concatenated JSON-array pages with `json.JSONDecoder.raw_decode`. A valid empty review array means no approval, never PASS. An API error or malformed response is BLOCKED.

## Trusted approval boundary

PR #1 was merged on 2026-11-23 08:22:44 UTC with `reviewDecision` empty in the captured `gh pr view` output. Its merge is a historical governance-code merge, not proof of independent review or WP1 acceptance. Check current complete review history using `gh api --paginate 'repos/studioraga/ai-enterprise-governed-lab/pulls/1/reviews'` (the script handles pagination).

Run on `review/wp1-release-authorization` worktree. Preserve original dirty `review/wp1-lab-acceptance` checkout and use only new worktree for commits. Current status remains M0 accepted, WP1 in progress, production denied.

The live gate requires externally administered reviewer eligibility, exact PR head approval, a nonempty collection of required passing checks, and correct branch. Independently controlled branch protection/rulesets and a real independent review are prerequisites: do not fabricate them. A local file and this script are not the sole trust root.

## Commands

```bash
cd "$WORKTREE"
python3 -m pytest -q tests
python3 scripts/check_no_production_claims.py
python3 scripts/wp1_pr_history_audit.py --root . --output "$AUDIT/history.json" || test "$?" -eq 2
gh api --paginate "repos/$REPO/pulls/1/reviews" > "$AUDIT/pr1-reviews-pages.json"
```

The local history audit deliberately exits 2 unless an independently allowlisted approval is actually found; never treat this as an automatic acceptance pass.

Before staging, inspect `git status --short --branch`. Commit and push **only** the new governance review branch. Open its new PR to `feature/wp1-kubernetes-integration` and freeze the head. Release promotion, protected merge, `main` release and tag are strictly conditional on subsequent independent approval and passing required checks.
