#!/usr/bin/env python3
"""Validate the canonical skills tree, including curated and compiled packages."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = ROOT / "skills"
errors: list[str] = []
seen_names: dict[str, Path] = {}
files = sorted(SKILLS_ROOT.rglob("SKILL.md"))
if not files:
    errors.append("no skills/**/SKILL.md files found")

for path in files:
    text = path.read_text(encoding="utf-8")
    relative = path.relative_to(ROOT)
    if not text.startswith("---\n"):
        errors.append(f"{relative}: missing YAML frontmatter")
        continue
    frontmatter_end = text.find("\n---\n", 4)
    if frontmatter_end == -1:
        errors.append(f"{relative}: unterminated YAML frontmatter")
        continue
    frontmatter = text[4:frontmatter_end]
    name_match = re.search(r"(?m)^name:\s*([^\n]+)", frontmatter)
    description_match = re.search(r"(?m)^description:\s*(.*)$", frontmatter)
    if not name_match or not name_match.group(1).strip():
        errors.append(f"{relative}: frontmatter missing name")
    else:
        name = name_match.group(1).strip().strip('"\'')
        previous = seen_names.get(name)
        if previous:
            errors.append(f"{relative}: duplicate skill name {name!r}; already used by {previous}")
        seen_names[name] = relative
    if not description_match:
        errors.append(f"{relative}: frontmatter missing description")
    for link in re.findall(r"\]\(([^)#]+)", text):
        if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", link):
            continue
        target = (path.parent / link).resolve()
        if not target.exists():
            errors.append(f"{relative}: broken relative link {link}")

for required in [SKILLS_ROOT / "SKILL.md", SKILLS_ROOT / "INDEX.md", SKILLS_ROOT / "_catalog/cangjie/README.md"]:
    if not required.exists():
        errors.append(f"missing required catalog file: {required.relative_to(ROOT)}")

if errors:
    print("Skill validation failed:")
    print("\n".join(f"- {error}" for error in errors))
    raise SystemExit(1)
print(f"validated {len(files)} Skill files, {len(seen_names)} unique names, and required catalog files")
