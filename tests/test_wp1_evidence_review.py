"""Regression checks for immutable, fail-closed WP1 evidence review."""
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from wp1_review_network_evidence import analyze

MARKERS = [
 'PASS: same namespace to protected Pod HTTP 200',
 'PASS: same namespace to unprotected control receiver HTTP 200',
 'PASS: other namespace to unprotected control receiver HTTP 200',
 'PASS: other namespace to protected Pod ingress denied; curl timeout exit 28',
 'PASS: protected application egress denied (socket timeout)',
 'BEHAVIORAL PASS: three positive HTTP controls and both selected-denial paths verified',
]


def bundle(tmp_path):
    src = tmp_path / 'probe.sh'
    src.write_text('#!/bin/sh\n')
    files = {
        'probe.log': '\n'.join(MARKERS) + '\nProtected Pod IPv4: 10.1.1.2; control receiver IPv4: 10.1.1.3\n',
        'probe-exit-code.txt': '0\n',
        'control-receiver-status.json': json.dumps({'name': 'wp1-control-receiver', 'labels': {'app': 'wp1-control-receiver'}, 'phase': 'Running', 'podIP': '10.1.1.3', 'conditions': [{'type': 'Ready', 'status': 'True'}]}),
        'application-pods.txt': 'app=feasibility-api app=wp1-control-receiver',
        'probe-pods.txt': 'wp1-other-ns',
        'networkpolicy.yaml': 'apiVersion: networking.k8s.io/v1\nkind: NetworkPolicy\nmetadata:\n  name: feasibility-api-deny-egress\nspec:\n  podSelector:\n    matchLabels:\n      app: feasibility-api\n  policyTypes: [Ingress, Egress]\n  ingress:\n    - from:\n        - podSelector: {}\n      ports:\n        - port: 8000\n          protocol: TCP\n',
        'kindnet-image.txt': 'docker.io/kindest/kindnetd:v20260820-69b56db7\n',
        'kindnet.log': 'normal reconciliation\n',
        'probe-source.sha256': hashlib.sha256(src.read_bytes()).hexdigest() + '  scripts/wp1_networkpolicy_probe.sh\n',
        'application-events.txt': 'Warning Startup probe failed wp1-control-receiver\n',
    }
    for n, content in files.items():
        (tmp_path / n).write_text(content)
    (tmp_path / 'SHA256SUMS').write_text(''.join(f'{hashlib.sha256((tmp_path / n).read_bytes()).hexdigest()}  ./{n}\n' for n in files))
    return src


def test_valid_bundle_is_pending_not_approved(tmp_path):
    src = bundle(tmp_path)
    result = analyze(tmp_path, src)
    assert result['status'] == 'PASS_PENDING_HUMAN_REVIEW'
    assert any('transient' in s for s in result['cautions'])


def test_tampering_rejected(tmp_path):
    src = bundle(tmp_path)
    (tmp_path / 'probe.log').write_text('modified')
    assert analyze(tmp_path, src)['status'] == 'FAIL'


def test_false_denial_rejected_even_with_rehashed_bundle(tmp_path):
    src = bundle(tmp_path)
    f = tmp_path / 'probe.log'
    f.write_text(f.read_text().replace('curl timeout exit 28', 'curl error exit 7'))
    entries = [x for x in (tmp_path / 'SHA256SUMS').read_text().splitlines() if not x.endswith('./probe.log')]
    entries.append(hashlib.sha256(f.read_bytes()).hexdigest() + '  ./probe.log')
    (tmp_path / 'SHA256SUMS').write_text('\n'.join(entries) + '\n')
    assert analyze(tmp_path, src)['status'] == 'FAIL'


def test_wrong_source_rejected(tmp_path):
    src = bundle(tmp_path)
    src.write_text('changed')
    assert analyze(tmp_path, src)['status'] == 'FAIL'


def test_receiver_label_scope_rejected(tmp_path):
    src = bundle(tmp_path)
    f = tmp_path / 'control-receiver-status.json'
    val = json.loads(f.read_text()); val['labels']['app'] = 'feasibility-api'; f.write_text(json.dumps(val))
    entries = [x for x in (tmp_path / 'SHA256SUMS').read_text().splitlines() if not x.endswith('./control-receiver-status.json')]
    entries.append(hashlib.sha256(f.read_bytes()).hexdigest() + '  ./control-receiver-status.json')
    (tmp_path / 'SHA256SUMS').write_text('\n'.join(entries) + '\n')
    assert analyze(tmp_path, src)['status'] == 'FAIL'


def test_rbac_script_is_read_only_and_fail_closed():
    script = (Path(__file__).resolve().parents[1] / 'scripts/wp1_rbac_secret_scope.sh').read_text()
    assert 'auth can-i' in script
    assert 'list secrets' in script and 'create deployments' in script
    assert 'get secrets' not in script and 'create secret' not in script
    assert 'automountServiceAccountToken == false' in script
    assert 'NOT_IMPLEMENTED: enterprise Secret rotation' in script
