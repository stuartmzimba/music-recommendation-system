#!/usr/bin/env python3
"""
Convenience entry point for running demo.py from root.
"""
import sys
import runpy
from pathlib import Path

# Fix Windows console UTF-8 output
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

target = Path(__file__).parent / "tools" / "demo.py"
runpy.run_path(str(target), run_name="__main__")
