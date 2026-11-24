#!/usr/bin/env bash
# Safe, deterministic preparation of a NEW approval PR after historical PR #1 merge.
# Never grants approval, merges, changes status, or creates a release tag.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
feature=feature/wp1-kubernetes-integration
new_branch=review/wp1-release-authorization
[[ -z "$(git status --porcelain)" ]] || { echo 'BLOCKED: uncommitted/untracked work'; exit 2; }
[[ "$(git branch --show-current)" == 'review/wp1-lab-acceptance' || "$(git branch --show-current)" == "$feature" ]] || {
  echo 'BLOCKED: unexpected current branch'; exit 2;
}
git fetch origin "$feature"
remote="$(git rev-parse "origin/$feature")"
[[ "$(git rev-parse "$feature")" == "$(git merge-base "$feature" "$remote")" ]] || {
  echo 'BLOCKED: local feature diverged; reconcile before fast-forward'; exit 2;
}
if git show-ref --verify --quiet "refs/heads/$new_branch"; then
  echo "BLOCKED: $new_branch exists. Inspect before reuse."; exit 2
fi
git switch "$feature"
git merge --ff-only "origin/$feature"
git switch -c "$new_branch"
printf 'PREPARED: %s based on %s\n' "$new_branch" "$(git rev-parse HEAD)"
printf 'NEXT: commit only the reviewed policy/approval-stage changes; create NEW PR into %s.\n' "$feature"
