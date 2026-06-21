#!/usr/bin/env python3
"""Run skill scripts with the detected Hermes-compatible Python."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from runtime import python_bin


SCRIPT_DIR = Path(__file__).resolve().parent


def build_command(script_name: str, args: list[str], *, python_exe: str | None = None) -> list[str]:
    script = Path(script_name)
    if script.is_absolute() or script.parent != Path("."):
        raise SystemExit("script must be a file name under scripts/, e.g. publish_pipe.py")
    script_path = SCRIPT_DIR / script
    if not script_path.exists() or script_path.suffix != ".py":
        raise SystemExit(f"unknown script: {script_name}")
    return [python_exe or python_bin(), str(script_path), *args]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a bundled script with runtime.python_bin().",
        usage="python scripts/run.py <script.py> [args...]",
    )
    parser.add_argument("script")
    parser.add_argument("args", nargs=argparse.REMAINDER)
    ns = parser.parse_args()
    env = os.environ.copy()
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("PYTHONIOENCODING", "utf-8")
    raise SystemExit(subprocess.call(build_command(ns.script, ns.args), env=env))


if __name__ == "__main__":
    main()
