import importlib.util
from pathlib import Path
spec = importlib.util.spec_from_file_location('live', Path(__file__).parents[1] / 'scripts/wp1_live_release_gate.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
SHA = 'a' * 40
PR = dict(state='OPEN', isDraft=False, baseRefName='feature/wp1-kubernetes-integration',
          headRefOid=SHA, reviewDecision='APPROVED', mergeable='MERGEABLE', author={'login': 'implementer'})
REV = [dict(id=1, user={'login': 'reviewer'}, state='APPROVED', commit_id=SHA, submitted_at='2026-11-23T07:00:00Z')]
CHECKS = [dict(name='governance-source', state='SUCCESS', bucket='pass')]

def evaluate(pr=None, reviews=None, checks=None, reviewers=None):
    return m.assess(PR if pr is None else pr, REV if reviews is None else reviews,
                    CHECKS if checks is None else checks, ['reviewer'] if reviewers is None else reviewers,
                    SHA, 'feature/wp1-kubernetes-integration')

def test_happy_path_only_ready_for_merge():
    out = evaluate()
    assert out['decision'] == 'READY_FOR_AUTHORIZED_MERGE'
    assert out['wp1_accepted'] is False and out['production_authorized'] is False

def test_no_required_checks_blocks():
    assert evaluate(checks=[])['decision'] == 'BLOCKED'

def test_failed_required_check_blocks():
    assert evaluate(checks=[dict(name='governance-source', bucket='fail')])['decision'] == 'BLOCKED'

def test_wrong_head_blocks():
    assert evaluate(pr={**PR, 'headRefOid': 'b'*40})['decision'] == 'BLOCKED'

def test_draft_blocks():
    assert evaluate(pr={**PR, 'isDraft': True})['decision'] == 'BLOCKED'

def test_self_review_blocks():
    return_reviews = [{**REV[0], 'user': {'login':'implementer'}}]
    assert evaluate(reviews=return_reviews, reviewers=['implementer'])['decision'] == 'BLOCKED'

def test_stale_review_blocks():
    assert evaluate(reviews=[{**REV[0], 'commit_id': 'b'*40}])['decision'] == 'BLOCKED'

def test_latest_changes_requested_blocks():
    reviews = REV + [{**REV[0], 'id':2, 'state':'CHANGES_REQUESTED', 'submitted_at':'2026-11-23T08:00:00Z'}]
    assert evaluate(reviews=reviews)['decision'] == 'BLOCKED'

def test_wrong_base_blocks():
    assert evaluate(pr={**PR, 'baseRefName':'main'})['decision'] == 'BLOCKED'

def test_missing_review_policy_blocks():
    assert evaluate(reviewers=[])['decision'] == 'BLOCKED'


def test_paginated_arrays_single_page():
    assert m.parse_gh_paginated_arrays('[{"id":1}]') == [{"id":1}]

def test_paginated_arrays_multiple_pages():
    assert m.parse_gh_paginated_arrays('[{"id":1}]\n[{"id":2}]') == [{"id":1}, {"id":2}]

def test_paginated_arrays_reject_non_array():
    import pytest
    with pytest.raises(ValueError):
        m.parse_gh_paginated_arrays('{"id":1}')

def test_paginated_arrays_empty_page_valid():
    assert m.parse_gh_paginated_arrays('[]') == []
