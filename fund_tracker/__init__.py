"""Fund tracker package shim.

We keep the code under ``fund_tracker/src`` to avoid packaging Python
modules alongside markdown/docs files.  To make ``python -m
fund_tracker.cli`` work without moving files, we tweak ``sys.path`` to
include the *src* directory at runtime.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure that submodules living under ``fund_tracker/src`` are discoverable as
# ``fund_tracker.<module>``. We do this by extending the package’s ``__path__``
# to include the *src* directory.

SRC_DIR = Path(__file__).resolve().parent / "src"

if SRC_DIR.is_dir():
    # 1) Add to global import search so ``import cli`` still works if someone
    #    runs the modules directly.
    sys.path.insert(0, str(SRC_DIR))

    # 2) Add to this package’s search path so ``import fund_tracker.cli`` works
    #    (import machinery will now look inside src/ for submodules).
    __path__.append(str(SRC_DIR))

del Path, sys, SRC_DIR
