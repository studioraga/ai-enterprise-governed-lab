"""Fail-closed state transition tests. Local receipt consistency != trusted approval."""
import copy
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('release_guard', ROOT / 'scripts/check_no_production_claims.py')
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


def fixture(tmp_path):
    q = tmp_path / 'qualification'
    q.mkdir()
    for name in ('status.json','wp1-lab-contract.json','wp1-secret-scope-exception.json'):
        (q/name).write_bytes((ROOT/'qualification'/name).read_bytes())
    return q


def save(q, name, value):
    (q/name).write_text(json.dumps(value))


def accepted(q):
    s = json.loads((q/'status.json').read_text())
    s['milestone']='WP1'
    s['work_packages'][0]['status']='accepted'
    save(q,'status.json',s)
    c=json.loads((q/'wp1-lab-contract.json').read_text())
    c['acceptance_status']='ACCEPTED_LAB'
    save(q,'wp1-lab-contract.json',c)
    e=json.loads((q/'wp1-secret-scope-exception.json').read_text())
    e['review_status']='APPROVED'
    save(q,'wp1-secret-scope-exception.json',e)
    receipt={'contract_id':'WP1-LAB-CONTRACT-v1','secret_exception_id':'WP1-EXCEPTION-SECRET-001',
        'decision':'APPROVED_LAB','production_authorized':False,
        'reviewed_source_commit':guard.RESEARCH,'network_probe_sha256':guard.PROBE,
        'network_evidence_manifest_sha256':guard.EVIDENCE,'reviewer':'external-reviewer',
        'implementer':'developer','reviewer_authority':'codeowner','reviewed_at':'2026-11-22T00:00:00Z',
        'approval_reference':'https://github.com/org/repo/pull/42#pullrequestreview-123'}
    save(q,'wp1-approval.json',receipt)
    return receipt


def blocked(q):
    try: guard.validate(q)
    except (AssertionError, KeyError, ValueError, FileNotFoundError): return
    assert False, 'guard should have rejected state'


def test_pending_m0_state(tmp_path):
    assert guard.validate(fixture(tmp_path))=='M0_ACCEPTED_WP1_PENDING'


def test_acceptance_without_receipt_fails(tmp_path):
    q=fixture(tmp_path);accepted(q); (q/'wp1-approval.json').unlink();blocked(q)


def test_stale_evidence_fails(tmp_path):
    q=fixture(tmp_path);r=accepted(q);r['network_evidence_manifest_sha256']='0'*64;save(q,'wp1-approval.json',r);blocked(q)


def test_wrong_source_fails(tmp_path):
    q=fixture(tmp_path);r=accepted(q);r['reviewed_source_commit']='0'*40;save(q,'wp1-approval.json',r);blocked(q)


def test_pending_exception_fails(tmp_path):
    q=fixture(tmp_path);accepted(q);e=json.loads((q/'wp1-secret-scope-exception.json').read_text());e['review_status']='PENDING';save(q,'wp1-secret-scope-exception.json',e);blocked(q)


def test_production_true_fails(tmp_path):
    q=fixture(tmp_path);accepted(q);s=json.loads((q/'status.json').read_text());s['production_authorized']=True;save(q,'status.json',s);blocked(q)


def test_future_wp_prematurely_accepted_fails(tmp_path):
    q=fixture(tmp_path);s=json.loads((q/'status.json').read_text());s['work_packages'][1]['status']='accepted';save(q,'status.json',s);blocked(q)


def test_self_review_fails(tmp_path):
    q=fixture(tmp_path);r=accepted(q);r['reviewer']='developer';save(q,'wp1-approval.json',r);blocked(q)


def test_valid_looking_local_receipt_only_passes_consistency(tmp_path):
    q=fixture(tmp_path);accepted(q)
    assert guard.validate(q)=='WP1_LAB_CONSISTENCY_ONLY_EXTERNAL_APPROVAL_REQUIRED'
