.PHONY: quality validate test security

quality: validate test security

validate:
	python3 tools/validate_skills.py

test:
	python3 -m compileall -q engine tools
	python3 -m pytest -q || test $$? -eq 5

security:
	@if command -v pip-audit >/dev/null 2>&1; then pip-audit -r engine/requirements.txt; else echo 'pip-audit not installed'; fi
	@if git grep -n -I -E 'github_pat_[A-Za-z0-9_]+|ghp_[A-Za-z0-9]+|AKIA[0-9A-Z]{16}|BEGIN (RSA|OPENSSH|EC|DSA|PGP) PRIVATE KEY'; then echo 'credential pattern detected'; exit 1; else echo 'no common credential patterns detected'; fi
