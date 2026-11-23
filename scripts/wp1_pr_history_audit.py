#!/usr/bin/env python3
"""Read-only audit of WP1 Git merge provenance and external PR review.

Does not create reviews, push branches, set acceptance status, or tag releases.
Offline results are never proof of GitHub reviewer independence.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

DEFAULT_REPO = 'studioraga/ai-enterprise-governed-lab'
BASE = 'feature/wp1-kubernetes-integration'
REVIEW_BRANCH = 'review/wp1-lab-acceptance'



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


def invoke(argv, cwd=None):
    cp = subprocess.run(argv, cwd=cwd, text=True, capture_output=True, check=False, timeout=30)
    if cp.returncode:
        raise RuntimeError(f'{argv[0]} {argv[1]} failed: {cp.stderr.strip()}')
    return cp.stdout.strip()

def inspect_graph(root):
    git = lambda *args: invoke(['git', *args], cwd=root)
    origin_feature = git('rev-parse', 'refs/remotes/origin/' + BASE)
    origin_review = git('rev-parse', 'refs/remotes/origin/' + REVIEW_BRANCH)
    local_feature = git('rev-parse', 'refs/heads/' + BASE)
    local_review = git('rev-parse', 'HEAD')
    contained = subprocess.run(['git', 'merge-base', '--is-ancestor', origin_review, origin_feature],cwd=root).returncode == 0
    status = git('status', '--porcelain')
    ahead = int(git('rev-list', '--count', f'{origin_feature}..{local_feature}'))
    behind = int(git('rev-list', '--count', f'{local_feature}..{origin_feature}'))
    return {'local_feature':local_feature,'remote_feature':origin_feature,
            'remote_review':origin_review,'checkout_head':local_review,
            'review_already_contained_in_feature':contained,
            'local_feature_ahead':ahead,'local_feature_behind':behind,
            'working_tree_clean':not bool(status)}

def assess(pr, reviews, graph, eligible):
    issues = []
    if pr.get('baseRefName') != BASE or pr.get('headRefName') != REVIEW_BRANCH:
        issues.append('PR branches do not match intended review')
    if pr.get('state') != 'MERGED' or not pr.get('mergedAt'):
        issues.append('historical PR is not confirmed merged')
    if pr.get('headRefOid') != graph['remote_review']:
        issues.append('PR reviewed head differs from recorded review branch')
    if not graph['review_already_contained_in_feature']:
        issues.append('review branch commits not contained in feature remote')
    author = (pr.get('author') or {}).get('login', '').casefold()
    latest = {}
    for rev in sorted(reviews, key=lambda r:(r.get('submitted_at') or '',r.get('id') or 0)):
        login = (rev.get('user') or {}).get('login','').casefold()
        if login: latest[login] = rev
    valid = [r for r in eligible if r.casefold() != author and
             (latest.get(r.casefold()) or {}).get('state') == 'APPROVED' and
             (latest.get(r.casefold()) or {}).get('commit_id') == pr.get('headRefOid')]
    if not eligible:
        issues.append('no independently governed reviewer allowlist supplied')
    if not valid:
        issues.append('no verified independent approval for exact historical PR head')
    return {'decision':'HISTORICAL_MERGE_REVIEWED' if not issues else 'REVIEW_PROVENANCE_BLOCKED',
            'issues':issues,'eligible_approvals':valid, 'production_authorized':False,
            'wp1_accepted':False}

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',type=Path,default=Path('.'))
    ap.add_argument('--repo',default=DEFAULT_REPO)
    ap.add_argument('--pr',type=int,default=1)
    ap.add_argument('--reviewer',action='append',default=[])
    ap.add_argument('--live',action='store_true',help='query GitHub through authenticated gh CLI')
    ap.add_argument('--output',type=Path)
    a=ap.parse_args(argv)
    try:
        graph=inspect_graph(a.root)
        result={'decision':'HISTORICAL_MERGE_FOUND' if graph['review_already_contained_in_feature'] else 'BRANCH_DIVERGENCE',
                'graph':graph,'production_authorized':False,'wp1_accepted':False}
        if a.live:
            pr=json.loads(invoke(['gh','pr','view',str(a.pr),'--repo',a.repo,'--json',
               'number,state,mergedAt,headRefOid,headRefName,baseRefName,author,mergeCommit,reviewDecision']))
            raw=invoke(['gh','api','--paginate',f'repos/{a.repo}/pulls/{a.pr}/reviews'])
            reviews=parse_gh_paginated_arrays(raw)
            result['review']=assess(pr,reviews,graph,a.reviewer)
            result['decision']=result['review']['decision']
        else:
            result['limitations']=['Offline graph only; no reviewer, branch protection, or CI verification']
    except (OSError,ValueError,RuntimeError,subprocess.TimeoutExpired) as exc:
        result={'decision':'BLOCKED','issues':[str(exc)],'production_authorized':False,'wp1_accepted':False}
    payload=json.dumps(result,indent=2)+'\n'
    print(payload,end='')
    if a.output:
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(payload)
    return 0 if result['decision']=='HISTORICAL_MERGE_REVIEWED' else 2
if __name__ == '__main__': sys.exit(main())
