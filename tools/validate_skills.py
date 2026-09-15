#!/usr/bin/env python3
"""Validate that every repository skill is loadable and internally linked."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
errors: list[str] = []
files = sorted((ROOT / "skills").glob("*/SKILL.md"))
root_skill = ROOT / "skills" / "SKILL.md"
if root_skill.exists() and root_skill not in files:
    files.insert(0, root_skill)
if not files:
    errors.append("no skills/*/SKILL.md files found")

for path in files:
    text = path.read_text(encoding="utf-8")
    relative = path.relative_to(ROOT)
    if not text.startswith("---\n"):
        errors.append(f"{relative}: missing YAML frontmatter")
        continue
    match = re.match(r"\A---\nname: ([^\n]+)\ndescription: ([^\n]+)\n---\n", text)
    if not match:
        errors.append(f"{relative}: frontmatter must contain name and description")
        continue
    if not match.group(1).strip() or len(match.group(2).strip()) < 40:
        errors.append(f"{relative}: name/description is too short")
    if len(text.splitlines()) > 500 and path.name == "SKILL.md":
        # Existing domain bodies are intentionally detailed; report rather than fail.
        print(f"warning: {relative} exceeds 500 lines", file=sys.stderr)
    for link in re.findall(r"\]\(([^)#]+)", text):
        target = (path.parent / link).resolve()
        if not target.exists():
            errors.append(f"{relative}: broken relative link {link}")

if errors:
    print("Skill validation failed:")
    print("\n".join(f"- {error}" for error in errors))
    raise SystemExit(1)
print(f"validated {len(files)} skill metadata files and relative links")
