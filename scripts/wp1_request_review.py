#!/usr/bin/env python3
"""Request a real GitHub reviewer through REST; never impersonates/approves."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--repo',required=True)
    ap.add_argument('--pr',type=int,required=True)
    ap.add_argument('--reviewers-file',type=Path,required=True)
    a=ap.parse_args()
    try:
        if not re.fullmatch(r'[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+',a.repo) or a.pr<1: raise ValueError('invalid target')
        if a.reviewers_file.is_symlink(): raise ValueError('symlink reviewer policy denied')
        reviewers=json.loads(a.reviewers_file.read_text())['reviewers']
        if not isinstance(reviewers,list) or not reviewers or any(not isinstance(x,str) or not x for x in reviewers): raise ValueError('invalid reviewer policy')
        pr=subprocess.run(['gh','api',f'repos/{a.repo}/pulls/{a.pr}'],text=True,capture_output=True,timeout=30)
        if pr.returncode: raise RuntimeError('failed to read GitHub pull request')
        author=(json.loads(pr.stdout).get('user') or {}).get('login','').casefold()
        if author in [r.casefold() for r in reviewers]: raise ValueError('PR author cannot review themselves')
        payload=json.dumps({'reviewers':reviewers})
        res=subprocess.run(['gh','api','-X','POST',f'repos/{a.repo}/pulls/{a.pr}/requested_reviewers','--input','-'],input=payload,text=True,capture_output=True,timeout=30)
        if res.returncode: raise RuntimeError('request failed: '+res.stderr.strip()[:300])
        print(json.dumps({'status':'REVIEW_REQUEST_SENT','reviewers':reviewers,'approved':False},indent=2))
        return 0
    except (ValueError,KeyError,OSError,RuntimeError,subprocess.TimeoutExpired) as ex:
        print(json.dumps({'status':'BLOCKED','reason':str(ex),'approved':False}))
        return 2

if __name__=='__main__':sys.exit(main())
