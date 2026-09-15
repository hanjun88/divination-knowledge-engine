#!/usr/bin/env python3
"""Check the local shell/Python environment required by this repository."""
from pathlib import Path
import shutil
import sys

root = Path(__file__).resolve().parents[1]
checks = {
    "python": sys.version_info >= (3, 11),
    "shell": shutil.which("bash") is not None,
    "git": shutil.which("git") is not None,
    "engine requirements": (root / "engine/requirements.txt").exists(),
    "skill validator": (root / "tools/validate_skills.py").exists(),
}
for name, ok in checks.items():
    print(f"{name}: {'ok' if ok else 'missing'}")
if not all(checks.values()):
    raise SystemExit(1)
print("environment: ready")
