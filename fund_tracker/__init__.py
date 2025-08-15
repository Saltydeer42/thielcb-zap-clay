"""Fund tracker package shim.

We keep the code under ``fund_tracker/src`` to avoid packaging Python
modules alongside markdown/docs files.  To make ``python -m
fund_tracker.cli`` work without moving files, we tweak ``sys.path`` to
include the *src* directory at runtime.
"""
from __future__ import annotations

import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent / "src"
if SRC_DIR.is_dir():
    sys.path.insert(0, str(SRC_DIR))

del Path, sys, SRC_DIR  # clean namespace
