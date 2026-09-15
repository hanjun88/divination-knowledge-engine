.PHONY: bootstrap env-check validate-skills python-check

PYTHON ?= python3
VENV ?= .venv

bootstrap:
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/python -m pip install --upgrade pip
	$(VENV)/bin/python -m pip install -r requirements-dev.txt
	$(VENV)/bin/python -m pip install -r engine/requirements.txt

env-check:
	$(PYTHON) tools/check_environment.py

validate-skills:
	$(PYTHON) tools/validate_skills.py

python-check:
	$(PYTHON) -m compileall -q engine tools

test: env-check validate-skills python-check
