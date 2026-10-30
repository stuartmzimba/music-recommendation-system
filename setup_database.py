#!/usr/bin/env python3
"""
Convenience entry point for database setup from root.
"""
import runpy
from pathlib import Path

target = Path(__file__).parent / "bin" / "setup_database.py"
runpy.run_path(str(target), run_name="__main__")
