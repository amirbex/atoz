#!/usr/bin/env python3
"""Compatibility validation entry point for the current AtoZ identity outputs."""
import subprocess
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
raise SystemExit(subprocess.call([sys.executable,str(ROOT/"tools/validate_brand_assets.py")],cwd=ROOT))
