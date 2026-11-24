import importlib.util
from pathlib import Path
import pytest

spec=importlib.util.spec_from_file_location('wp1live', Path(__file__).parents[1]/'scripts/wp1_live_release_gate.py')
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
SHA='a'*40
BASE='feature/wp1-kubernetes-integration'
PR={'state':'open','draft':False,'head':{'sha':SHA},'base':{'ref':BASE},'user':{'login':'implementer'},'mergeable':True,'mergeable_state':'clean'}
REV=[{'id':1,'user':{'login':'approved-reviewer'},'state':'APPROVED','commit_id':SHA,'submitted_at':'2026-11-23T10:00:00Z'}]
PROTECTION={'required_pull_request_reviews':{'required_approving_review_count':1,'dismiss_stale_reviews':True},'required_status_checks':{'contexts':['governance-source']},'enforce_admins':{'enabled':True},'allow_force_pushes':{'enabled':False},'allow_deletions':{'enabled':False}}
RUNS={'total_count':1,'check_runs':[{'id':100,'name':'governance-source','head_sha':SHA,'status':'completed','conclusion':'success'}]}
STATUSES={'sha':SHA,'statuses':[]}

def check(pr=PR,reviews=REV,protection=PROTECTION,runs=RUNS,statuses=STATUSES,reviewers=None):
    return m.assess(pr,reviews,protection,runs,statuses,['approved-reviewer'] if reviewers is None else reviewers,SHA,BASE)

def test_happy_path_not_release():
    r=check(); assert r['decision']=='READY_FOR_AUTHORIZED_MERGE'
    assert r['wp1_accepted'] is False and r['production_authorized'] is False

def test_zero_rules_block():
    assert check(protection={})['decision']=='BLOCKED'

def test_optional_check_not_enough():
    assert check(protection={**PROTECTION,'required_status_checks':{'contexts':[]}})['decision']=='BLOCKED'

def test_required_check_failed():
    assert check(runs={'total_count':1,'check_runs':[{**RUNS['check_runs'][0],'conclusion':'failure'}]})['decision']=='BLOCKED'

def test_required_check_missing():
    assert check(runs={'total_count':0,'check_runs':[]})['decision']=='BLOCKED'

def test_check_runs_paginated_not_complete():
    assert check(runs={'total_count':101,'check_runs':RUNS['check_runs']})['decision']=='BLOCKED'

def test_unprotected_approval_does_not_count():
    assert check(protection={**PROTECTION,'required_pull_request_reviews':None})['decision']=='BLOCKED'

def test_self_review():
    rev=[{**REV[0],'user':{'login':'implementer'}}]
    assert check(reviews=rev,reviewers=['implementer'])['decision']=='BLOCKED'

def test_stale_review():
    assert check(reviews=[{**REV[0],'commit_id':'b'*40}])['decision']=='BLOCKED'

def test_changes_requested():
    reviews=REV+[{**REV[0],'id':2,'state':'CHANGES_REQUESTED','submitted_at':'2026-11-23T11:00:00Z'}]
    assert check(reviews=reviews)['decision']=='BLOCKED'

def test_head_mismatch():
    assert check(pr={**PR,'head':{'sha':'b'*40}})['decision']=='BLOCKED'

def test_wrong_base():
    assert check(pr={**PR,'base':{'ref':'main'}})['decision']=='BLOCKED'

def test_force_push_allowed():
    assert check(protection={**PROTECTION,'allow_force_pushes':{'enabled':True}})['decision']=='BLOCKED'

def test_status_context_success():
    runs={'total_count':0,'check_runs':[]}
    statuses={'sha':SHA,'statuses':[{'context':'governance-source','state':'success'}]}
    assert check(runs=runs,statuses=statuses)['decision']=='READY_FOR_AUTHORIZED_MERGE'

def test_no_reviewer_policy():
    assert check(reviewers=[])['decision']=='BLOCKED'

def test_pagination():
    assert m.paginated_arrays('[]\n[{"id":1}]')==[{'id':1}]
    with pytest.raises(ValueError):m.paginated_arrays('{}')


def test_admins_must_be_protected():
    assert check(protection={**PROTECTION, 'enforce_admins': {'enabled': False}})['decision'] == 'BLOCKED'

def test_failing_check_run_not_masked_by_legacy_success():
    failing = {'total_count': 1, 'check_runs': [{**RUNS['check_runs'][0], 'conclusion': 'failure'}]}
    success_status = {'sha': SHA, 'statuses': [{'context': 'governance-source', 'state': 'success'}]}
    assert check(runs=failing, statuses=success_status)['decision'] == 'BLOCKED'
