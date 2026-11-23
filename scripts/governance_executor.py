#!/usr/bin/env python3
"""Illustrative bounded, non-mutating executor for untrusted AI proposals.

Not an authentication or privilege boundary. Do NOT run as a privileged service.
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {
    'verify_baseline': ['bash', 'scripts/verify_baseline.sh'],
    'verify_m0': ['python3', 'scripts/verify_m0_compose_record.py', '--require-evidence'],
    'verify_wp1_contract': ['python3', 'scripts/wp1_lab_gate.py', '--root', '.'],
    'check_release_boundary': ['python3', 'scripts/check_no_production_claims.py'],
}


def authorize(proposal):
    if not isinstance(proposal, dict) or set(proposal) != {'milestone', 'action', 'requested_release'}:
        return None, 'invalid proposal schema'
    if proposal['milestone'] != 'WP1' or proposal['requested_release'] is not False:
        return None, 'release or milestone scope not permitted'
    if not isinstance(proposal['action'], str) or proposal['action'] not in ALLOWED:
        return None, 'action not allowlisted'
    return ALLOWED[proposal['action']], None


def execute(proposal, runner=subprocess.run):
    command, reason = authorize(proposal)
    if reason:
        return {'decision': 'DENY', 'reason': reason, 'production_authorized': False}
    try:
        result = runner(command, cwd=ROOT, capture_output=True, text=True,
                        timeout=120, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {'decision':'FAIL','reason':type(exc).__name__, 'production_authorized':False}
    return {'decision': 'PASS' if result.returncode == 0 else 'FAIL',
            'action': proposal['action'], 'exit_code': result.returncode,
            'stdout_tail': result.stdout[-2000:], 'stderr_tail': result.stderr[-2000:],
            'production_authorized': False}


if __name__ == '__main__':
    try:
        data = json.load(sys.stdin)
        result = execute(data)
    except (ValueError, TypeError, json.JSONDecodeError):
        result = {'decision': 'DENY', 'reason': 'malformed JSON', 'production_authorized': False}
    print(json.dumps(result, indent=2))
    sys.exit(0 if result['decision'] == 'PASS' else 1)
