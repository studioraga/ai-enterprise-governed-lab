#!/usr/bin/env python3
"""Read-only, fail-closed GitHub approval and required-check gate for WP1 LAB PRs.

Never merges, approves, tags, changes branch protection, or updates project state.
The reviewer policy must be maintained independently of the PR under review.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

_SHA = re.compile(r"^[a-f0-9]{40}$")
_REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")




def parse_gh_paginated_arrays(raw):
    """Parse concatenated JSON arrays emitted by `gh api --paginate`.

    Compatible with older gh versions without --slurp; reject incomplete output.
    """
    decoder = json.JSONDecoder()
    pos = 0
    pages = []
    while pos < len(raw):
        while pos < len(raw) and raw[pos].isspace():
            pos += 1
        if pos >= len(raw):
            break
        page, pos = decoder.raw_decode(raw, pos)
        if not isinstance(page, list):
            raise ValueError('GitHub reviews page is not a JSON array')
        pages.extend(page)
    if not pages and not raw.strip():
        raise ValueError('empty GitHub reviews response')
    return pages


def run_gh(*args):
    result = subprocess.run(['gh', *args], text=True, capture_output=True, timeout=30, check=False)
    if result.returncode:
        raise RuntimeError(f"GitHub query failed ({args[0]}): {result.stderr.strip()[:500]}")
    if args[0] == 'api' and '--paginate' in args:
        return parse_gh_paginated_arrays(result.stdout)
    return json.loads(result.stdout)


def assess(pr, reviews, checks, reviewers, expected_head, expected_base):
    issues = []
    if pr.get('state') != 'OPEN' or pr.get('isDraft') is not False:
        issues.append('PR not open and ready for review')
    if pr.get('baseRefName') != expected_base:
        issues.append('PR base mismatch')
    if not _SHA.fullmatch(str(expected_head)) or pr.get('headRefOid') != expected_head:
        issues.append('PR head mismatch or invalid frozen SHA')
    author = ((pr.get('author') or {}).get('login') or '').casefold()
    if not author:
        issues.append('PR author missing')
    if pr.get('reviewDecision') != 'APPROVED':
        issues.append('GitHub reviewDecision is not APPROVED')
    if pr.get('mergeable') != 'MERGEABLE':
        issues.append('PR is not currently mergeable')
    last = {}
    for review in sorted(reviews, key=lambda r: (r.get('submitted_at') or '', r.get('id') or 0)):
        login = ((review.get('user') or {}).get('login') or '').casefold()
        if login:
            last[login] = review
    qualified = []
    for reviewer in reviewers:
        login = reviewer.casefold()
        review = last.get(login, {})
        if login != author and review.get('state') == 'APPROVED' and review.get('commit_id') == expected_head:
            qualified.append(reviewer)
    if not reviewers or not qualified:
        issues.append('no exact-head approval from independently allowlisted reviewer')
    if not checks:
        issues.append('no required CI checks configured or returned')
    else:
        for check in checks:
            name = check.get('name', '<unnamed>')
            if check.get('bucket') != 'pass':
                issues.append(f'required check not passing: {name} ({check.get("bucket")})')
    return {
        'decision': 'READY_FOR_AUTHORIZED_MERGE' if not issues else 'BLOCKED',
        'issues': issues,
        'approved_reviewers': qualified,
        'required_checks': len(checks),
        'wp1_accepted': False,
        'production_authorized': False,
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', required=True)
    p.add_argument('--pr', required=True, type=int)
    p.add_argument('--base', required=True)
    p.add_argument('--expected-head', required=True)
    p.add_argument('--reviewers-file', required=True, type=Path)
    p.add_argument('--output', type=Path)
    args = p.parse_args(argv)
    try:
        if not _REPO.fullmatch(args.repo) or args.pr < 1 or not _SHA.fullmatch(args.expected_head):
            raise ValueError('invalid repository, PR number, or frozen commit SHA')
        if args.reviewers_file.is_symlink():
            raise ValueError('reviewer policy symlinks are not allowed')
        obj = json.loads(args.reviewers_file.read_text())
        reviewers = obj.get('reviewers')
        if not isinstance(reviewers, list) or not reviewers or not all(isinstance(r, str) and r.strip() for r in reviewers):
            raise ValueError('no valid external reviewer policy')
        pr = run_gh('pr', 'view', str(args.pr), '-R', args.repo, '--json',
                    'state,isDraft,baseRefName,headRefOid,reviewDecision,mergeable,author')
        raw = run_gh('api', '--paginate', f'repos/{args.repo}/pulls/{args.pr}/reviews')
        reviews = raw
        checks = run_gh('pr', 'checks', str(args.pr), '-R', args.repo, '--required', '--json', 'name,state,bucket')
        result = assess(pr, reviews, checks, reviewers, args.expected_head, args.base)
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        result = {'decision': 'BLOCKED', 'issues': [str(exc)], 'wp1_accepted': False, 'production_authorized': False}
    result_text = json.dumps(result, indent=2) + '\n'
    print(result_text, end='')
    if args.output:
        if args.output.is_symlink():
            print('Refusing symlinked output', file=sys.stderr)
            return 2
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(result_text)
    return 0 if result['decision'] == 'READY_FOR_AUTHORIZED_MERGE' else 2

if __name__ == '__main__':
    sys.exit(main())
