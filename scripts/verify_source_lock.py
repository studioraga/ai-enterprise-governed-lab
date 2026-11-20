#!/usr/bin/env python3
"""Schema and source-pointer check. Offline source hashes require optional archive paths."""
import json, pathlib, sys
p=pathlib.Path(__file__).resolve().parents[1]/'provenance/source-lock.json'
x=json.loads(p.read_text())
assert x['schema']=='ai-enterprise-import-provenance-v1'
assert len(x['source_archives'])==2
for source in x['source_archives']:
    assert len(source['sha256'])==64 and len(source['head'])==40
    assert source['repository'] and source['working_tree']
print('source lock structure: PASS (not an archive-integrity recheck)')
