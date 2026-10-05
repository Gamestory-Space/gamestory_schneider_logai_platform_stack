#!/usr/bin/env python3
"""Compatibility entry point delegating to the shipped Compose lifecycle wrapper."""
import argparse
import subprocess
from pathlib import Path
parser=argparse.ArgumentParser(description='Configure runtime credentials in the Compose env file; reconciliation is automatic.')
parser.add_argument('--env-file',type=Path,required=True)
args=parser.parse_args()
subprocess.run([str(Path(__file__).resolve().parents[1]/'client/deploy-compose.sh'),str(args.env_file)],check=True)
