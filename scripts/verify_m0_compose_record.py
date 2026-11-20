#!/usr/bin/env python3
"""Check M0 qualification record format; separately check local evidence files when present."""
from pathlib import Path
import json, subprocess, sys
root=Path(__file__).resolve().parents[1]
record=json.loads((root/'qualification/m0-compose-local.json').read_text())
status=json.loads((root/'qualification/status.json').read_text())
assert record['overall']=='PASS'
assert record['production_authorized'] is False
assert record['wp1_status']=='NOT_RUN'
assert status['production_authorized'] is False
assert status['local_qualifications']['wp1_kubernetes']=='NOT_RUN'
missing=[]
for e in record['runs']:
    d=root/e['evidence_bundle_local_path']
    if d.is_dir():
        proc=subprocess.run(['sha256sum','-c','SHA256SUMS'],cwd=d,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        if proc.returncode:
            print(proc.stdout,proc.stderr,file=sys.stderr);sys.exit(1)
        print(f"Evidence {e['id']}: PASS ({e['files_verified']} files)")
    else:
        missing.append(e['id'])
        print(f"Evidence {e['id']}: NOT_PRESENT, verify separately on Node1 (not a pass)")
if missing and '--require-evidence' in sys.argv:
    sys.exit('FAIL: local evidence missing: ' + ', '.join(missing))
print('M0 Compose record structure: PASS; evidence: ' + ('NOT_PRESENT' if missing else 'PASS') + '; WP1 NOT_RUN; production denied')
