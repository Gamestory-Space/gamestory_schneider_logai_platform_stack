#!/usr/bin/env python3
"""Scan without embedding or printing a forbidden bootstrap credential."""
import hashlib
import re
from pathlib import Path

# Match candidate printable credential strings, including inside binaries/URLs.
CANDIDATES=re.compile(rb'(?=([a-z]{5}\.[a-z]{2}))')


def forbidden(data,digest):
    return any(hashlib.sha256(match.group(1)).hexdigest()==digest for match in CANDIDATES.finditer(data))


def scan_paths(paths,digest):
    violations=[]
    for root in paths:
        files=root.rglob('*') if root.is_dir() else [root]
        for file in files:
            if file.is_file() and forbidden(file.read_bytes(),digest):violations.append(str(file))
    if violations:raise ValueError('Forbidden bootstrap credential material detected; contents suppressed')


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--digest-file',type=Path,required=True);parser.add_argument('paths',type=Path,nargs='+');args=parser.parse_args()
    scan_paths(args.paths,args.digest_file.read_text().strip());print('PASS: no forbidden bootstrap credential material detected')
