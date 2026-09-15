FROM mcr.microsoft.com/vscode/devcontainers/python:3.12-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends make git bash \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspaces/divination-knowledge-engine
