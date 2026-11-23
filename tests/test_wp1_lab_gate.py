"""Regression checks for the read-only WP1 acceptance proposal gate."""
import copy
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('wp1_lab_gate', ROOT / 'scripts/wp1_lab_gate.py')
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)


def pr():
    return {'head': {'sha': 'a'*40}, 'base': {'ref':'feature/wp1-kubernetes-integration'},
            'state':'open', 'draft':False, 'user':{'login':'implementer'}}


def reviews():
    return [{'id':1,'submitted_at':'2026-11-21T10:00:00Z', 'user':{'login':'reviewer'},
             'state':'APPROVED', 'commit_id':'a'*40}]


def test_local_pending_is_review_ready():
    assert g.verify_local(ROOT)['decision'] == 'READY_FOR_INDEPENDENT_REVIEW'


def test_external_review_of_exact_head_only():
    assert g.verify_github_review(pr(), reviews(), expected_base='feature/wp1-kubernetes-integration',
        expected_head='a'*40, allowed_reviewers=['reviewer'])['decision'] == 'READY_FOR_HUMAN_MERGE_REVIEW'


def test_wrong_sha_blocks():
    assert g.verify_github_review(pr(), reviews(), expected_base='feature/wp1-kubernetes-integration',
        expected_head='b'*40, allowed_reviewers=['reviewer'])['decision']=='BLOCKED'


def test_self_approval_blocks():
    r=reviews();r[0]['user']['login']='implementer'
    assert g.verify_github_review(pr(),r,expected_base='feature/wp1-kubernetes-integration',
        expected_head='a'*40,allowed_reviewers=['implementer'])['decision']=='BLOCKED'


def test_stale_or_dismissed_review_blocks():
    r=reviews()+[{'id':2,'submitted_at':'2026-11-21T10:01:00Z', 'user':{'login':'reviewer'},
                    'state':'DISMISSED', 'commit_id':'a'*40}]
    assert g.verify_github_review(pr(),r,expected_base='feature/wp1-kubernetes-integration',
        expected_head='a'*40,allowed_reviewers=['reviewer'])['decision']=='BLOCKED'


def test_wrong_base_blocks():
    assert g.verify_github_review(pr(),reviews(),expected_base='main',expected_head='a'*40,
        allowed_reviewers=['reviewer'])['decision']=='BLOCKED'


def test_missing_approval_blocks():
    assert g.verify_github_review(pr(),[],expected_base='feature/wp1-kubernetes-integration',
        expected_head='a'*40,allowed_reviewers=['reviewer'])['decision']=='BLOCKED'


def test_original_evidence_manifest_is_optional_offline_but_verified_if_provided(tmp_path):
    assert g.verify_local(ROOT, tmp_path)['decision']=='BLOCKED'
