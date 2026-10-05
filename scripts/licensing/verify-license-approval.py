#!/usr/bin/env python3
"""Publication-only gate for explicit Gamestory approval of the exact licence bytes."""
import argparse,hashlib,json
from datetime import datetime
from pathlib import Path

def validate(license_text,approval):
    digest=hashlib.sha256(license_text).hexdigest()
    if approval.get('owner')!='Gamestory Ltd' or approval.get('status')!='approved':
        raise ValueError('Gamestory approval of the final licence text is pending; publication is blocked')
    if approval.get('sha256')!=digest:raise ValueError('Licence changed after approval; publication is blocked')
    if not isinstance(approval.get('approvedBy'),str) or not approval['approvedBy'].strip():raise ValueError('Approval identity is missing')
    try:timestamp=datetime.fromisoformat(approval['approvedAt'].replace('Z','+00:00'))
    except (ValueError,TypeError,KeyError):raise ValueError('Approval timestamp is missing or invalid') from None
    if timestamp.tzinfo is None:raise ValueError('Approval timestamp must include timezone')
    return {'status':'approved','owner':'Gamestory Ltd','sha256':digest}

def main():
    p=argparse.ArgumentParser();p.add_argument('--license-file',type=Path,required=True);p.add_argument('--approval-file',type=Path,required=True);args=p.parse_args()
    try:result=validate(args.license_file.read_bytes(),json.loads(args.approval_file.read_text()))
    except (ValueError,OSError) as exc:raise SystemExit(str(exc)) from None
    print(json.dumps(result))

if __name__=='__main__':main()
