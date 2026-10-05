#!/usr/bin/env python3
"""Canonical licence and synchronized build/tooling snapshots without legal approval inference."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('--local-snapshots',action='store_true');args=p.parse_args()
text=(ROOT/'LICENSE').read_bytes();approval=json.loads((ROOT/'licensing/approval.json').read_text())
assert text.strip() and b'GAMESTORY PROPRIETARY CLOSED-SOURCE SOFTWARE LICENSE' in text and b'Gamestory Ltd' in text
assert approval['sha256']==hashlib.sha256(text).hexdigest() and approval['status'] in ['pending-review','approved']
assert (ROOT/'THIRD_PARTY_NOTICES').read_bytes().strip()
if args.local_snapshots:
    for name,context in [('gamestory-identity-kit','backend'),('gamestory-logai-api',''),('logai_ui','')]:
        repo=ROOT.parent/name;build=repo/context
        assert (build/'LICENSE').read_bytes()==text,name+' licence snapshot drift'
        assert (build/'licensing/NOTICE').read_bytes()==(ROOT/'THIRD_PARTY_NOTICES').read_bytes(),name+' notice drift'
        assert json.loads((build/'licensing/approval.json').read_text())==approval,name+' approval drift'
        if context:assert (repo/'LICENSE').read_bytes()==text
        for file in ['verify-image-license.py','test-image-license.py','verify-license-approval.py','test-license-approval.py']:
            assert (repo/'scripts/release'/file).read_bytes()==(ROOT/'scripts/licensing'/file).read_bytes(),name+' tooling drift'
print('PASS: canonical licence, digest-bound review state and requested snapshots')
