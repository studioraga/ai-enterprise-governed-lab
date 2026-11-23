import importlib.util
from pathlib import Path
spec=importlib.util.spec_from_file_location('audit', Path(__file__).parents[1]/'scripts/wp1_pr_history_audit.py')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
BASE={'remote_review':'a'*40,'review_already_contained_in_feature':True}
PR={'state':'MERGED','mergedAt':'2026-11-23T08:22:00Z','baseRefName':m.BASE,
    'headRefName':m.REVIEW_BRANCH,'headRefOid':'a'*40,'author':{'login':'implementer'}}
REV=[{'user':{'login':'reviewer'},'state':'APPROVED','commit_id':'a'*40,
      'submitted_at':'2026-11-23T08:21:00Z','id':1}]
def test_historical_merge_needs_external_reviewer():
    assert m.assess(PR,REV,BASE,[])['decision']=='REVIEW_PROVENANCE_BLOCKED'
def test_exact_head_independent_review():
    assert m.assess(PR,REV,BASE,['reviewer'])['decision']=='HISTORICAL_MERGE_REVIEWED'
def test_wrong_sha_blocks():
    assert m.assess(PR,[{**REV[0],'commit_id':'b'*40}],BASE,['reviewer'])['decision']=='REVIEW_PROVENANCE_BLOCKED'
def test_self_review_blocks():
    assert m.assess(PR,[{**REV[0],'user':{'login':'implementer'}}],BASE,['implementer'])['decision']=='REVIEW_PROVENANCE_BLOCKED'
def test_superseded_review_blocks():
    reviews=REV+[{'user':{'login':'reviewer'},'state':'CHANGES_REQUESTED','commit_id':'a'*40,
                  'submitted_at':'2026-11-23T08:22:00Z','id':2}]
    assert m.assess(PR,reviews,BASE,['reviewer'])['decision']=='REVIEW_PROVENANCE_BLOCKED'
def test_unmerged_blocks():
    assert m.assess({**PR,'state':'OPEN','mergedAt':None},REV,BASE,['reviewer'])['decision']=='REVIEW_PROVENANCE_BLOCKED'


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
