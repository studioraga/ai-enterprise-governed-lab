#!/usr/bin/env python3
"""Ensure rebranding is complete without rewriting historical Git metadata."""
from pathlib import Path
import json
import re

root = Path(__file__).resolve().parents[1]
# Construct historical prefixes to avoid carrying stale identifiers as project constants.
old_prefix = 'i' + 'g'
legacy = re.compile(r'(?i)\b' + old_prefix + r'(?:[-_ ](?:labs|feasibility)|[-_](?!nore))')
# The specific second part above purposely catches stray old-prefixed names.
failures = []
for file in root.rglob('*'):
    if '.git' in file.parts or file.is_dir():
        continue
    if legacy.search(str(file.relative_to(root))):
        failures.append(f'legacy path: {file.relative_to(root)}')
    try:
        content = file.read_text(encoding='utf-8')
    except (UnicodeDecodeError, OSError):
        continue
    for n, line in enumerate(content.splitlines(), 1):
        if legacy.search(line):
            failures.append(f'{file.relative_to(root)}:{n}: legacy project marker')

source = json.loads((root / 'provenance/source-lock.json').read_text())
status = json.loads((root / 'qualification/status.json').read_text())
if source.get('schema') != 'ai-enterprise-import-provenance-v1':
    failures.append('source-lock.json schema mismatch')
if status.get('schema') != 'ai-enterprise-qualification-v1':
    failures.append('qualification/status.json schema mismatch')
if status.get('production_authorized') is not False:
    failures.append('production authorization must remain false')
if failures:
    raise SystemExit('\n'.join(failures))
print('project identity audit: PASS (project sources, not historical .git records)')
