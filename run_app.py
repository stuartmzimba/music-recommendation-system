#!/usr/bin/env python3
"""
Compatibility shim for running the canonical launcher in `bin/`.

Keep calling `python run_app.py` from the repository root — this script forwards
execution to `bin/run_app_launcher.py` so the codebase keeps a single canonical
launcher implementation under `bin/` while preserving the old entrypoint.
"""

import runpy
import sys
from pathlib import Path

# Ensure bin is on sys.path so the module can be executed reliably
BASE = Path(__file__).parent
BIN_LAUNCHER = BASE / "bin" / "run_app_launcher.py"

if not BIN_LAUNCHER.exists():
    print("ERROR: launcher not found at bin/run_app_launcher.py")
    sys.exit(1)

# Execute the relocated launcher as a script
runpy.run_path(str(BIN_LAUNCHER), run_name="__main__")
