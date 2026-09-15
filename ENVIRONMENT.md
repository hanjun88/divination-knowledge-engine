# Repository execution environment

This repository supports a reproducible shell/Python environment through `.devcontainer/` or a local virtual environment. On a local machine run `make bootstrap`, then `make test`. The environment check is `make env-check`; the Skill tree validator is `make validate-skills`.

The repository currently contains no `step6-a/` directory and therefore cannot execute audit scripts from that path until those scripts are added to the repository or checked out from their source repository.
