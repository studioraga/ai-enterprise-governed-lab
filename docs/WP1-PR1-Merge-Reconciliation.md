# WP1 PR #1 reconciliation / Step 14.5.3 correction

**Historical state (2026-11-23 archive):** `origin/feature/wp1-kubernetes-integration` already contains `review/wp1-lab-acceptance` through merge commit `f0ee81cc645ca0960d23dc954c03325b57d0655a`. The local feature branch is still at `d9c80c2`. The old review head is `44270d9bdcbe400413527f6e2cbaa8aa81f49604`.

This was a **governance framework merge**, not an independently approved WP1 lab acceptance. The accepted milestone remains M0; contract and Secret exception remain pending; production is denied.

## Automated safe sequence

1. Check old merged PR and Git provenance. `gh pr view 1 --json state,mergedAt,mergedBy,baseRefName,headRefName,headRefOid,mergeCommit,reviewDecision` and `gh api repos/studioraga/ai-enterprise-governed-lab/pulls/1/reviews`. `gh pr list` defaults to open; it will not display the merged PR. Do not recreate PR #1.
2. Execute `python3 scripts/wp1_pr_history_audit.py --root . --live --pr 1 --reviewer <independently-administered-reviewer-login>`. An unknown/absent reviewer remains BLOCKED. A PASS is historical review provenance only, **not** WP1 acceptance.
3. Verify clean working tree. Run `bash scripts/wp1_start_acceptance_review.sh`. This fast-forwards the local feature branch to the existing remote merge and creates a *new* branch `review/wp1-release-authorization`. It does not push, merge, approve, or tag.
4. Prepare a distinct acceptance change with reviewed contract, exception disposition, approval receipt tied to a real external approval, status change, and negative-policy regression tests. Keep M0 historical record intact. Run tests and commit on the new branch.
5. Create a **new** PR from `review/wp1-release-authorization` into `feature/wp1-kubernetes-integration` only when the new branch has commits, and require a designated independent reviewer to approve the exact final head.
6. Enforce GitHub branch rules/required checks. The human or designated authorized release service performs the GitHub approval and merge. No local JSON field can synthesize an approval. Verify post-merge commit, open a separate protected PR into main if required, test final main commit, and only then release-custodian tag `v0.2.0-wp1-lab`.
7. Begin WP2 with independent `WP2-LAB-CONTRACT-v1` and separately checked milestone entry.

## Hard stops

- Historical PR #1 may have been merged without the required independent review. **Do not backdate an approval.** Record the deficiency and require a fresh authorized review of the final WP1 release PR.
- No remote GitHub review, no eligible reviewer, wrong commit, missing evidence, failed tests, changed Secret scope, absent branch rule, or missing release authority => BLOCKED.
- A GitHub admin or the original author merging PR #1 does not prove independent acceptance.
- The working-tree evidence bundle may contain private data. Share only sanitized evidence or hashes; never share kubeconfig or raw Secrets.
- GitHub checks must be required under configured branch/ruleset policy; this sample does not install organization-wide rulesets or grant reviewers.

## Verification commands

```bash
# Show merged PR (the old PR is NOT open)
gh pr view 1 --repo studioraga/ai-enterprise-governed-lab --json number,state,mergedAt,mergedBy,headRefOid,baseRefName,mergeCommit,reviewDecision
# Exact local ancestry and branch pointers
git fetch origin
git log --graph --oneline --decorate --all -15
git merge-base --is-ancestor origin/review/wp1-lab-acceptance origin/feature/wp1-kubernetes-integration
# Read-only graph audit
python3 scripts/wp1_pr_history_audit.py --root .
# Additional live review check (requires independently administered reviewer identity)
python3 scripts/wp1_pr_history_audit.py --root . --live --pr 1 --reviewer <approved-github-login>
# Once working tree is clean, prepare NEW acceptance review branch
bash scripts/wp1_start_acceptance_review.sh
```

The automation must not alter `qualification/status.json`, the current M0 tag, or GitHub remote branches without independently satisfied gates.
