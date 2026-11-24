#!/usr/bin/env python3
"""Offline, synthetic-only governance test. Never creates GitHub approval or reviewer policy."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('wp1_live_release_gate', BASE / 'wp1_live_release_gate.py')
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
SHA = 'a' * 40
BRANCH = 'feature/wp1-kubernetes-integration'


def scenarios():
    pr = {'state':'open', 'draft': False, 'head':{'sha':SHA},
          'base':{'ref':BRANCH}, 'user':{'login':'synthetic-author'},
          'mergeable':True, 'mergeable_state':'clean'}
    protection = {'enforce_admins':{'enabled':True},
                  'required_pull_request_reviews':{'required_approving_review_count':1,'dismiss_stale_reviews':True},
                  'required_status_checks':{'contexts':['governance-source']},
                  'allow_force_pushes':{'enabled':False},'allow_deletions':{'enabled':False}}
    runs = {'total_count':1,'check_runs':[{'id':1,'name':'governance-source','head_sha':SHA,
             'status':'completed','conclusion':'success'}]}
    statuses = {'sha':SHA,'statuses':[]}
    approved = [{'id':1,'user':{'login':'synthetic-independent-reviewer'}, 'state':'APPROVED',
                'commit_id':SHA, 'submitted_at':'2026-01-01T00:00:00Z'}]
    eligible = ['synthetic-independent-reviewer']
    cases = {
        'synthetic_happy_path': (pr, approved, protection, runs, statuses, eligible, 'READY_FOR_AUTHORIZED_MERGE'),
        'missing_approval': (pr, [], protection, runs, statuses, eligible, 'BLOCKED'),
        'wrong_source_sha': ({**pr, 'head':{'sha':'b'*40}}, approved, protection, runs, statuses, eligible, 'BLOCKED'),
        'missing_required_checks': (pr, approved, {**protection,'required_status_checks':None},runs,statuses,eligible,'BLOCKED'),
        'missing_protection': (pr,approved,{},runs,statuses,eligible,'BLOCKED'),
        'self_review': ({**pr,'user':{'login':'synthetic-independent-reviewer'}}, approved, protection,runs,statuses,eligible,'BLOCKED'),
        'failing_check': (pr,approved,protection,{'total_count':1,'check_runs':[{**runs['check_runs'][0],'conclusion':'failure'}]},statuses,eligible,'BLOCKED'),
    }
    outcomes = {}
    for name, (p,r,b,c,s,reviewers,expected) in cases.items():
        decision = gate.assess(p,r,b,c,s,reviewers,SHA,BRANCH)['decision']
        outcomes[name] = {'decision':decision,'expected':expected,'passed':decision==expected}
    return outcomes


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    results=scenarios()
    report={'kind':'SYNTHETIC_TEST_ONLY','trusted_review':False,'github_approval':False,
            'wp1_accepted':False,'production_authorized':False,
            'simulation_tests_passed':all(r['passed'] for r in results.values()),'scenarios':results}
    raw=json.dumps(report,indent=2)+'\n'
    print(raw,end='')
    if args.output:
        if args.output.is_symlink():
            print('Refusing symlink output',file=sys.stderr)
            return 2
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(raw)
    return 0 if report['simulation_tests_passed'] else 2

if __name__=='__main__':
    raise SystemExit(main())
