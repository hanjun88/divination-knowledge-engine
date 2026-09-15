FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

COPY engine/requirements.txt /tmp/requirements.txt
RUN python -m pip install --upgrade pip && python -m pip install -r /tmp/requirements.txt pytest ruff pip-audit
WORKDIR /workspaces/divination-knowledge-engine
