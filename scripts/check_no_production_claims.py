#!/usr/bin/env python3
"""Versioned LAB milestone state consistency check. NOT an approval oracle.

Approved receipts are locally forgeable: GitHub/branch-protection verification MUST
be independently enforced by release workflow before any merge or tag.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
Q = ROOT / 'qualification'
PROBE = '3666263ae78d52f41bb7392eeb188d53b54f1d29054fdfb66ebfbd28a229fb68'
EVIDENCE = '5a779eff4429a056855621b7946d797fdad09719da099c8fffd041b21a23695c'
RESEARCH = 'd9c80c264a9b6ce7e4767fed58b009f56b0d91e7'


def validate(q=Q):
    status = json.loads((q / 'status.json').read_text())
    assert status['production_authorized'] is False
    assert status.get('local_qualifications', {}).get('production_authorized') is False
    packages = status['work_packages']
    assert sorted(x['id'] for x in packages) == [f'WP{i}' for i in range(1, 7)]
    by_id = {x['id']: x for x in packages}
    assert all(by_id[f'WP{i}']['status'] != 'accepted' for i in range(2, 7))
    wp1 = by_id['WP1']['status']
    if wp1 in ('planned', 'in_progress'):
        assert status['milestone'] == 'M0'
        return 'M0_ACCEPTED_WP1_PENDING'
    assert wp1 == 'accepted' and status['milestone'] == 'WP1'
    contract = json.loads((q / 'wp1-lab-contract.json').read_text())
    exception = json.loads((q / 'wp1-secret-scope-exception.json').read_text())
    receipt = json.loads((q / 'wp1-approval.json').read_text())
    assert contract['contract_id'] == 'WP1-LAB-CONTRACT-v1'
    assert contract['acceptance_status'] == 'ACCEPTED_LAB'
    assert contract['production_authorized'] is False
    assert 'independent_reviewer_approval' in contract['required_gates']
    assert contract['exceptions']['application_secret_provisioning']['disposition'] == 'NOT_APPLICABLE'
    assert exception['id'] == 'WP1-EXCEPTION-SECRET-001'
    assert exception['contract_id'] == contract['contract_id']
    assert exception['review_status'] == 'APPROVED'
    assert exception['proposed_disposition'] == 'NOT_APPLICABLE'
    assert exception['production_authorized'] is False
    assert receipt['contract_id'] == contract['contract_id']
    assert receipt['secret_exception_id'] == exception['id']
    assert receipt['decision'] == 'APPROVED_LAB'
    assert receipt['production_authorized'] is False
    assert receipt['reviewed_source_commit'] == RESEARCH
    assert receipt['network_probe_sha256'] == PROBE
    assert receipt['network_evidence_manifest_sha256'] == EVIDENCE
    assert receipt['reviewer'] != receipt.get('implementer')
    for key in ('reviewer', 'reviewer_authority', 'approval_reference', 'reviewed_at', 'reviewed_source_commit'):
        assert isinstance(receipt.get(key), str) and receipt[key].strip()
    assert re.fullmatch(r'[0-9a-f]{40}', receipt['reviewed_source_commit'])
    assert receipt['approval_reference'].startswith('https://github.com/')
    return 'WP1_LAB_CONSISTENCY_ONLY_EXTERNAL_APPROVAL_REQUIRED'


if __name__ == '__main__':
    print('production release boundary: PASS; ' + validate() + '; production denied')
