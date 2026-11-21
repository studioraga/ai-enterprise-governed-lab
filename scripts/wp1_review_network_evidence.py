#!/usr/bin/env python3
"""Offline, fail-closed assessment of the exact WP1 v5.3 differential test bundle.

Does not connect to Kubernetes or authorize WP1; it checks integrity and consistency
of operator-collected evidence. Human independence is a separate approval gate.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

EXPECTED = (
    'PASS: same namespace to protected Pod HTTP 200',
    'PASS: same namespace to unprotected control receiver HTTP 200',
    'PASS: other namespace to unprotected control receiver HTTP 200',
    'PASS: other namespace to protected Pod ingress denied; curl timeout exit 28',
    'PASS: protected application egress denied (socket timeout)',
    'BEHAVIORAL PASS: three positive HTTP controls and both selected-denial paths verified',
)
FILES = ('probe.log', 'probe-exit-code.txt', 'networkpolicy.yaml',
         'control-receiver-status.json', 'application-pods.txt',
         'probe-pods.txt', 'kindnet-image.txt', 'kindnet.log',
         'probe-source.sha256', 'application-events.txt', 'SHA256SUMS')


def analyze(bundle: Path, source: Path | None = None) -> dict:
    issues = []
    cautions = []
    if not bundle.is_dir():
        return {'status': 'FAIL', 'issues': ['evidence directory missing'], 'cautions': []}
    for name in FILES:
        if not (bundle / name).is_file():
            issues.append(f'missing required {name}')
    if issues:
        return {'status': 'FAIL', 'issues': issues, 'cautions': cautions}
    manifest = (bundle / 'SHA256SUMS').read_text(encoding='utf-8')
    checked = set()
    for line in manifest.splitlines():
        m = re.fullmatch(r'([0-9a-f]{64})  (\.?/?[^\n]+)', line)
        if not m:
            issues.append('malformed SHA256SUMS entry')
            continue
        digest, name = m.groups()
        rel = Path(name)
        if rel.is_absolute() or '..' in rel.parts or rel.name == 'SHA256SUMS':
            issues.append(f'unsafe manifest filename: {name}')
            continue
        f = bundle / rel
        if f.is_symlink() or not f.is_file():
            issues.append(f'missing/symlinked evidence: {name}')
        elif hashlib.sha256(f.read_bytes()).hexdigest() != digest:
            issues.append(f'checksum mismatch: {name}')
        checked.add(rel.name)
    for required in FILES:
        if required != 'SHA256SUMS' and required not in checked:
            issues.append(f'required file omitted from manifest: {required}')
    if (bundle / 'probe-exit-code.txt').read_text().strip() != '0':
        issues.append('probe exit status not zero')
    log = (bundle / 'probe.log').read_text(errors='replace')
    for marker in EXPECTED:
        if marker not in log:
            issues.append(f'probe marker missing: {marker}')
    ip_match = re.search(r'Protected Pod IPv4: (\d+\.\d+\.\d+\.\d+); control receiver IPv4: (\d+\.\d+\.\d+\.\d+)', log)
    if not ip_match or ip_match.group(1) == ip_match.group(2):
        issues.append('missing or non-distinct tested Pod IPs')
    try:
        receiver = json.loads((bundle / 'control-receiver-status.json').read_text())
        if receiver.get('name') != 'wp1-control-receiver':
            issues.append('unexpected control receiver identity')
        if receiver.get('labels', {}).get('app') != 'wp1-control-receiver':
            issues.append('control receiver label selects wrong application')
        if receiver.get('phase') != 'Running' or not any(
            x.get('type') == 'Ready' and x.get('status') == 'True'
            for x in receiver.get('conditions', [])):
            issues.append('control receiver not reported Ready')
        if ip_match and receiver.get('podIP') != ip_match.group(2):
            issues.append('receiver IP mismatch between probe and status')
    except (ValueError, TypeError) as exc:
        issues.append(f'bad receiver status JSON: {exc}')
    app = (bundle / 'application-pods.txt').read_text(errors='replace')
    other = (bundle / 'probe-pods.txt').read_text(errors='replace')
    if 'app=feasibility-api' not in app or 'app=wp1-control-receiver' not in app:
        issues.append('missing application and control receiver label evidence')
    if 'wp1-other-ns' not in other:
        issues.append('missing other-namespace client evidence')
    policy = (bundle / 'networkpolicy.yaml').read_text(errors='replace')
    try:
        import yaml
        obj = yaml.safe_load(policy)
        spec = obj['spec']
        if obj['kind'] != 'NetworkPolicy' or obj['metadata']['name'] != 'feasibility-api-deny-egress':
            issues.append('unexpected policy identity')
        if spec.get('podSelector', {}).get('matchLabels', {}).get('app') != 'feasibility-api':
            issues.append('unexpected policy Pod selector')
        if not {'Ingress', 'Egress'}.issubset(spec.get('policyTypes', [])):
            issues.append('missing ingress/egress policy types')
        if spec.get('egress', []) != []:
            issues.append('egress not deny-all')
        ingress = spec.get('ingress', [])
        if len(ingress) != 1 or ingress[0].get('from') != [{'podSelector': {}}] or ingress[0].get('ports') != [{'port': 8000, 'protocol': 'TCP'}]:
            issues.append('unexpected same-namespace ingress scope')
    except (ImportError, KeyError, TypeError, ValueError) as exc:
        issues.append(f'cannot validate NetworkPolicy YAML: {exc}')
    source_record = (bundle / 'probe-source.sha256').read_text().strip().split()
    if len(source_record) < 2 or not re.fullmatch('[0-9a-f]{64}', source_record[0]):
        issues.append('bad probe source checksum record')
    elif source:
        if not source.is_file() or hashlib.sha256(source.read_bytes()).hexdigest() != source_record[0]:
            issues.append('probe source differs from recorded test script')
    else:
        cautions.append('tested source bytes not compared to local script; pass --source')
    try:
        events = (bundle / 'application-events.txt').read_text(errors='replace')
        warnings = [line for line in events.splitlines() if 'Warning' in line]
        for line in warnings:
            if 'Startup probe failed' in line and 'wp1-control-receiver' in line:
                cautions.append('transient receiver startup warning; corroborate later Ready and HTTP controls')
            else:
                cautions.append('unclassified Kubernetes warning requires reviewer inspection')
    except OSError:
        cautions.append('application events missing; reviewer should retrieve original')
    summary = (bundle / 'qualification-summary.md')
    if summary.exists() and 'TO_BE_VERIFIED' in summary.read_text():
        cautions.append('operator summary still contains placeholders; do not publish as accepted')
    cautions.append('offline consistency is not independent approval or production authorization')
    return {'status': 'PASS_PENDING_HUMAN_REVIEW' if not issues else 'FAIL',
            'issues': issues, 'cautions': sorted(set(cautions)),
            'checks': {'five_traffic_paths': not any('probe marker' in x for x in issues),
                       'manifest_integrity': not any('manifest' in x or 'checksum' in x or 'evidence' in x for x in issues),
                       'policy_contract': not any('policy' in x or 'egress' in x or 'ingress' in x for x in issues)}}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--source', type=Path, help='exact locally tested probe script')
    parser.add_argument('--output', type=Path, help='write JSON to a separate review folder')
    args = parser.parse_args()
    result = analyze(args.evidence, args.source)
    payload = json.dumps(result, indent=2) + '\n'
    print(payload, end='')
    if args.output:
        if args.output.resolve().is_relative_to(args.evidence.resolve()):
            parser.error('output must be outside immutable original evidence directory')
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload)
    return 0 if result['status'] == 'PASS_PENDING_HUMAN_REVIEW' else 1


if __name__ == '__main__':
    sys.exit(main())
