# Development

This repo uses **uv** for dependency management, **Ruff** for lint/format, and **ty** for type checking.

## Prerequisites

- Python 3.12 (see `.python-version`)
- uv (recommended)

If you use the devcontainer, uv is pre-installed and the environment is created automatically.

## Setup

```bash
uv sync --dev
```

This creates/updates the project virtual environment (default: `.venv`) and installs dev tools.

## Lint / Format / Type check

Run the same checks as CI:

```bash
uv run ruff check src
uv run ruff format --check src
uv run ty check src
```

Auto-fix lint and apply formatting:

```bash
uv run ruff check --fix src
uv run ruff format src
```

## pre-commit

Install hooks once:

```bash
uv run pre-commit install
```

Run on all files:

```bash
uv run pre-commit run --all-files
```

Note: If Ruff fixes files during a commit, re-stage the changes (`git add`) and re-run the commit.

## CI

GitHub Actions runs:

- `ruff check src`
- `ruff format --check src`
- `ty check src`

See `.github/workflows/lint.yml`.
