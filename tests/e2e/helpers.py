"""Shared helpers for live e2e CLI tests."""

import shutil
import subprocess
import sys


def run_annocli(*args, check=True):
    """Run the annocli entrypoint via the current Python interpreter."""
    cmd = [sys.executable, "-m", "annocli.cli", *args]
    # Prefer installed console script when available
    if shutil.which("annocli"):
        cmd = ["annocli", *args]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise AssertionError(
            f"Command failed ({result.returncode}): {' '.join(cmd)}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result
