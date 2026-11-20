#!/usr/bin/env python3
"""Protect against accidentally marking WP0 as production accepted."""
import json, pathlib
p=pathlib.Path(__file__).resolve().parents[1]/'qualification/status.json'
s=json.loads(p.read_text())
assert s['production_authorized'] is False
assert s['milestone']=='M0'
assert all(x['status']!='accepted' for x in s['work_packages'])
print('production release boundary: PASS')
