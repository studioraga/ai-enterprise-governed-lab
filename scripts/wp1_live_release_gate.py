#!/usr/bin/env python3
"""Fail-closed WP1 PR readiness verifier (not a release or production authorization).

Uses GitHub REST for approvals, branch protection, and required check-run/status
results. Never trusts a local approval receipt as independent authority.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import quote

_SHA = re.compile(r'^[0-9a-f]{40}$')
_REPO = re.compile(r'^[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+$')


def paginated_arrays(raw):
    decoder = json.JSONDecoder()
    pos, out, seen = 0, [], False
    while pos < len(raw):
        while pos < len(raw) and raw[pos].isspace(): pos += 1
        if pos == len(raw): break
        obj, pos = decoder.raw_decode(raw, pos)
        if not isinstance(obj, list): raise ValueError('paginated page must be an array')
        out.extend(obj); seen = True
    if not seen: raise ValueError('empty paginated response')
    return out


def gh_json(*args, paginate=False):
    command = ['gh', 'api'] + (['--paginate'] if paginate else []) + list(args)
    proc = subprocess.run(command, text=True, capture_output=True, timeout=45, check=False)
    if proc.returncode: raise RuntimeError('GitHub API failed: ' + proc.stderr.strip()[:350])
    return paginated_arrays(proc.stdout) if paginate else json.loads(proc.stdout)


def assess(pr, reviews, protection, check_runs, statuses, reviewers, expected_head, expected_base):
    problems = []
    head = (pr.get('head') or {}).get('sha')
    author = ((pr.get('user') or {}).get('login') or '').casefold()
    if pr.get('state') != 'open' or pr.get('draft') is not False:
        problems.append('PR is closed or draft')
    if (pr.get('base') or {}).get('ref') != expected_base:
        problems.append('PR base branch mismatch')
    if not _SHA.fullmatch(expected_head) or head != expected_head:
        problems.append('PR head differs from frozen SHA')
    if not author: problems.append('PR author missing')
    if pr.get('mergeable') is not True or pr.get('mergeable_state') not in ('clean', 'unstable'):
        problems.append('PR not confirmed mergeable by GitHub')

    required_reviews = (protection or {}).get('required_pull_request_reviews') or {}
    needed = required_reviews.get('required_approving_review_count')
    if not isinstance(needed, int) or needed < 1:
        problems.append('branch protection has no required approving review')
        needed = 1
    if not required_reviews.get('dismiss_stale_reviews') and not required_reviews.get('require_last_push_approval'):
        problems.append('branch protection lacks stale-review/last-push guard')
    if ((protection or {}).get('allow_force_pushes') or {}).get('enabled') is True:
        problems.append('branch permits force pushes')
    if ((protection or {}).get('allow_deletions') or {}).get('enabled') is True:
        problems.append('branch permits deletion')

    latest = {}
    for rev in sorted(reviews, key=lambda r:(r.get('submitted_at') or '', r.get('id') or 0)):
        login = ((rev.get('user') or {}).get('login') or '').casefold()
        if login: latest[login] = rev
    eligible = {r.casefold() for r in reviewers if isinstance(r, str) and r.strip()}
    approvals = [login for login,rev in latest.items()
                 if login in eligible and login != author and rev.get('state') == 'APPROVED'
                 and rev.get('commit_id') == head]
    if len(approvals) < needed:
        problems.append('insufficient independent exact-head approvals')

    required = (protection or {}).get('required_status_checks') or {}
    contexts = required.get('contexts') or []
    checks_v2 = required.get('checks') or []
    required_names = set(contexts) | {x.get('context') for x in checks_v2 if isinstance(x,dict)}
    required_names.discard(None)
    if not required_names:
        problems.append('branch protection has no required checks')
    if not any('governance-source' in n for n in required_names):
        problems.append('governance-source is not required by branch protection')
    if not isinstance(check_runs, dict) or check_runs.get('total_count', 0) > len(check_runs.get('check_runs',[])):
        problems.append('check runs incomplete or malformed')
    latest_checks = {}
    for c in (check_runs.get('check_runs',[]) if isinstance(check_runs,dict) else []):
        name = c.get('name')
        if name and c.get('head_sha') == head:
            if name not in latest_checks or c.get('id',0) > latest_checks[name].get('id',0):
                latest_checks[name] = c
    latest_status = {}
    for st in (statuses.get('statuses',[]) if isinstance(statuses,dict) else []):
        ctx = st.get('context')
        if ctx and ctx not in latest_status: latest_status[ctx] = st
    if not isinstance(statuses,dict) or statuses.get('sha') != head:
        problems.append('combined commit-status response references another SHA')
    for name in sorted(required_names):
        run = latest_checks.get(name)
        st = latest_status.get(name)
        if run and run.get('status') == 'completed' and run.get('conclusion') == 'success':
            continue
        if st and st.get('state') == 'success':
            continue
        problems.append('required check missing or non-success: ' + name)
    return {'decision': 'READY_FOR_AUTHORIZED_MERGE' if not problems else 'BLOCKED',
            'issues': problems, 'approved_reviewers': approvals,
            'required_checks': sorted(required_names), 'wp1_accepted': False,
            'production_authorized': False}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', required=True)
    p.add_argument('--pr', type=int, required=True)
    p.add_argument('--base', required=True)
    p.add_argument('--expected-head', required=True)
    p.add_argument('--reviewers-file', type=Path, required=True)
    p.add_argument('--output', type=Path)
    a = p.parse_args(argv)
    try:
        if not _REPO.fullmatch(a.repo) or a.pr < 1 or not _SHA.fullmatch(a.expected_head):
            raise ValueError('invalid repo/PR/frozen SHA')
        if a.reviewers_file.is_symlink(): raise ValueError('symlink reviewer policy denied')
        policy = json.loads(a.reviewers_file.read_text())
        reviewers = policy.get('reviewers')
        if not isinstance(reviewers,list) or not reviewers or not all(isinstance(x,str) and x.strip() for x in reviewers):
            raise ValueError('missing authorized reviewer policy')
        base_path = f'repos/{a.repo}'
        pr = gh_json(f'{base_path}/pulls/{a.pr}')
        reviews = gh_json(f'{base_path}/pulls/{a.pr}/reviews?per_page=100', paginate=True)
        encoded = quote(a.base,safe='')
        protection = gh_json(f'{base_path}/branches/{encoded}/protection')
        runs = gh_json(f'{base_path}/commits/{a.expected_head}/check-runs?per_page=100')
        statuses = gh_json(f'{base_path}/commits/{a.expected_head}/status')
        result = assess(pr,reviews,protection,runs,statuses,reviewers,a.expected_head,a.base)
    except (OSError,ValueError,RuntimeError,subprocess.TimeoutExpired,KeyError,TypeError,json.JSONDecodeError) as exc:
        result = {'decision':'BLOCKED','issues':[str(exc)],'wp1_accepted':False,'production_authorized':False}
    output = json.dumps(result,indent=2)+'\n'
    print(output,end='')
    if a.output:
        if a.output.is_symlink():
            print('Refusing symlink output', file=sys.stderr)
            return 2
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(output)
    return 0 if result['decision']=='READY_FOR_AUTHORIZED_MERGE' else 2

if __name__ == '__main__': sys.exit(main())
