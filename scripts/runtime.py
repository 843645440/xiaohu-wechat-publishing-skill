#!/usr/bin/env python3
"""Runtime helpers: find the right Python interpreter & TTY detection.

Solves the recurring pain that some hosts have runtime packages installed
under /usr/bin/python3.12 but NOT under /usr/bin/python3 (3.10 / 3.11).

Public API:
    python_bin()  -> str  # absolute path of a Python interpreter that satisfies
                          # min version AND has core formatting dependencies.
    is_tty()      -> bool # whether stdout is a real terminal (vs. pipe / agent run)
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from functools import lru_cache

REQUIRED_MODS = ("markdown",)
CANDIDATES = (
    os.environ.get("HERMES_PYTHON"),
    "python3.14", "python3.13", "python3.12", "python3.11", "python3.10",
    "python3", sys.executable,
)


def _probe(binary: str) -> bool:
    if not binary:
        return False
    path = shutil.which(binary) or (binary if os.path.isabs(binary) and os.path.isfile(binary) else None)
    if not path:
        return False
    code = (
        "import sys\n"
        "ok = sys.version_info >= (3, 9)\n"
        "import importlib.util as u\n"
        "ok = ok and all(u.find_spec(m) is not None for m in "
        + repr(list(REQUIRED_MODS))
        + ")\n"
        "raise SystemExit(0 if ok else 1)\n"
    )
    try:
        r = subprocess.run([path, "-c", code], capture_output=True, timeout=8)
        return r.returncode == 0
    except Exception:
        return False


@lru_cache(maxsize=1)
def python_bin() -> str:
    """Return absolute path of a Python interpreter that has all required modules.

    Falls back to sys.executable with a warning if nothing better is found.
    """
    seen = set()
    for cand in CANDIDATES:
        if not cand or cand in seen:
            continue
        seen.add(cand)
        if _probe(cand):
            return shutil.which(cand) or cand
    # nothing matched — return current interpreter, caller will hit ImportError later
    return sys.executable


def is_tty() -> bool:
    try:
        return sys.stdout.isatty() and sys.stdin.isatty()
    except Exception:
        return False


if __name__ == "__main__":
    print(python_bin())
