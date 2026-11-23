#!/usr/bin/env python3
"""Read-only, fail-closed WP1 laboratory gates. Never grants production authority.

AI recommendations are untrusted. The deterministic gate validates only evidence
and external reviewer state; merge/tag/promotion remain separate human-controlled acts.
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

EXPECTED_CONTRACT = "WP1-LAB-CONTRACT-v1"
EXPECTED_PROBE = "3666263ae78d52f41bb7392eeb188d53b54f1d29054fdfb66ebfbd28a229fb68"
EXPECTED_MANIFEST = "5a779eff4429a056855621b7946d797fdad09719da099c8fffd041b21a23695c"
EXPECTED_GATES = {
    "helm_static_render", "kind_deployment_readiness", "controlled_failed_image_rollout",
    "helm_rollback_recovery", "synthetic_http_positive_negative_tests",
    "networkpolicy_five_path_differential_test", "serviceaccount_token_and_workload_security",
    "rbac_secret_list_denied", "rbac_deployment_create_denied",
    "evidence_integrity_and_source_provenance", "independent_reviewer_approval",
}
EXCLUSIONS = {"real_oidc_jwks_authentication", "managed_secret_rotation_and_revocation",
              "external_secret_provider_integration", "production_high_availability",
              "production_tenant_isolation"}


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_local(root, evidence=None):
    root = Path(root)
    problems = []
    status = read_json(root / 'qualification/status.json')
    contract = read_json(root / 'qualification/wp1-lab-contract.json')
    exception = read_json(root / 'qualification/wp1-secret-scope-exception.json')
    packages = {p['id']: p for p in status['work_packages']}
    if status.get('milestone') != 'M0' or status.get('production_authorized') is not False:
        problems.append('baseline must remain M0; production denied')
    if packages.get('WP1', {}).get('status') != 'in_progress':
        problems.append('WP1 must remain in progress before authorized promotion')
    if any(packages.get(f'WP{i}', {}).get('status') == 'accepted' for i in range(2, 7)):
        problems.append('a future work package was prematurely accepted')
    if contract.get('contract_id') != EXPECTED_CONTRACT or contract.get('acceptance_status') != 'PENDING_REVIEW':
        problems.append('unexpected contract or premature contract acceptance')
    if contract.get('production_authorized') is not False:
        problems.append('contract claims production authority')
    if len(contract.get('required_gates', [])) != len(EXPECTED_GATES) or set(contract.get('required_gates', [])) != EXPECTED_GATES:
        problems.append('required gate inventory changed')
    if not EXCLUSIONS.issubset(set(contract.get('not_implemented', []))):
        problems.append('enterprise exclusions missing')
    if contract.get('exceptions', {}).get('application_secret_provisioning', {}).get('disposition') != 'NOT_APPLICABLE':
        problems.append('fixture applicability inconsistent')
    if exception.get('id') != 'WP1-EXCEPTION-SECRET-001' or exception.get('contract_id') != EXPECTED_CONTRACT:
        problems.append('exception identity/contract mismatch')
    if exception.get('proposed_disposition') != 'NOT_APPLICABLE' or exception.get('review_status') != 'PENDING':
        problems.append('exception improperly promoted')
    if exception.get('production_authorized') is not False:
        problems.append('exception claims production authority')
    if evidence is not None:
        ev = Path(evidence)
        m = ev / 'SHA256SUMS'
        if not m.is_file() or sha256(m) != EXPECTED_MANIFEST:
            problems.append('original evidence manifest missing/mismatched')
        else:
            check = subprocess.run(['sha256sum', '-c', 'SHA256SUMS'], cwd=ev,
                                   capture_output=True, text=True, check=False)
            if check.returncode != 0:
                problems.append('evidence file checksum verification failed')
        probe = (ev / 'probe-source.sha256')
        if not probe.is_file() or not probe.read_text().split() or probe.read_text().split()[0] != EXPECTED_PROBE:
            problems.append('probe evidence hash mismatch')
        source = root / 'scripts/wp1_networkpolicy_probe.sh'
        if not source.is_file() or sha256(source) != EXPECTED_PROBE:
            problems.append('tested probe source no longer matches')
    return {'decision': 'READY_FOR_INDEPENDENT_REVIEW' if not problems else 'BLOCKED',
            'issues': problems, 'production_authorized': False,
            'wp1_accepted': False}


def verify_github_review(pr, reviews, *, expected_base, expected_head, allowed_reviewers):
    """Evaluate fresh GitHub REST API responses; no local receipt can substitute."""
    issues = []
    head = pr.get('head', {}).get('sha')
    author = pr.get('user', {}).get('login')
    if pr.get('base', {}).get('ref') != expected_base:
        issues.append('wrong pull request base')
    if head != expected_head or not re.fullmatch(r'[0-9a-f]{40}', str(head)):
        issues.append('PR head differs from frozen reviewed commit')
    if pr.get('state') != 'open' or pr.get('draft', False):
        issues.append('PR is closed or draft')
    # Last review by each reviewer, not any stale historical approval.
    last = {}
    for review in sorted(reviews, key=lambda x: (x.get('submitted_at') or '', x.get('id') or 0)):
        login = review.get('user', {}).get('login')
        if login:
            last[login.casefold()] = review
    approved = []
    for reviewer in allowed_reviewers:
        rev = last.get(reviewer.casefold())
        if (reviewer.casefold() != str(author).casefold() and rev
            and rev.get('state') == 'APPROVED' and rev.get('commit_id') == head):
            approved.append(reviewer)
    if not approved:
        issues.append('no eligible independent approval of exact current PR head')
    return {'decision': 'READY_FOR_HUMAN_MERGE_REVIEW' if not issues else 'BLOCKED',
            'issues': issues, 'qualifying_reviewers': approved,
            'production_authorized': False, 'wp1_accepted': False}


def gh_api(endpoint):
    # --slurp produces one JSON array across paginated responses.
    paginated = endpoint.endswith('/reviews')
    cmd = ['gh', 'api'] + (['--paginate', '--slurp'] if paginated else []) + [endpoint]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode:
        raise RuntimeError('GitHub API unavailable or unauthorized: ' + result.stderr.strip())
    parsed = json.loads(result.stdout)
    if paginated:
        return [item for page in parsed for item in page]
    return parsed


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', default='.')
    p.add_argument('--evidence', help='original unmodified v5.3 evidence directory')
    p.add_argument('--github-pr', type=int, help='read live GitHub approval for this PR')
    p.add_argument('--repo', help='owner/repo; required with --github-pr')
    p.add_argument('--reviewer', action='append', default=[], help='trusted independent reviewer login (repeatable)')
    p.add_argument('--base', default='feature/wp1-kubernetes-integration')
    p.add_argument('--expected-head', help='exact 40-character frozen PR head SHA')
    a = p.parse_args(argv)
    try:
        report = verify_local(a.root, a.evidence)
        if a.github_pr:
            if not a.evidence:
                p.error('--evidence is required for any live review claim')
            if not (a.repo and a.reviewer and a.expected_head):
                p.error('--repo, --reviewer, and --expected-head required for GitHub review')
            if report['issues']:
                print(json.dumps(report, indent=2)); return 1
            prefix = f'repos/{a.repo}/pulls/{a.github_pr}'
            remote = verify_github_review(gh_api(prefix), gh_api(prefix + '/reviews'),
                      expected_base=a.base, expected_head=a.expected_head,
                      allowed_reviewers=a.reviewer)
            report = {'local': report, 'remote': remote,
                      'decision': remote['decision'], 'production_authorized': False,
                      'wp1_accepted': False}
        print(json.dumps(report, indent=2))
        return 0 if report['decision'] in ('READY_FOR_INDEPENDENT_REVIEW', 'READY_FOR_HUMAN_MERGE_REVIEW') else 1
    except (OSError, KeyError, ValueError, RuntimeError, json.JSONDecodeError) as e:
        print(json.dumps({'decision':'BLOCKED', 'issues':[str(e)], 'wp1_accepted':False,
                          'production_authorized':False}, indent=2))
        return 1


if __name__ == '__main__':
    sys.exit(main())
