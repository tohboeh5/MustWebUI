# AGENTS

This document defines the required quality gates for humans and automation (CI, pre-commit, and coding agents).

## Non-negotiable checks

Before opening a PR (or when making changes as an agent), ensure all of the following pass:

```bash
uv run ruff check src
uv run ruff format --check src
uv run ty check src
```

If you changed Python sources, you must run the checks above at minimum.

## Auto-fix policy

Preferred workflow:

```bash
uv run ruff check --fix src
uv run ruff format src
```

Then re-run the non-fix checks.

## pre-commit policy

- The repository pins hook versions in `.pre-commit-config.yaml`.
- Developers should install hooks locally:

```bash
uv run pre-commit install
```

- Running hooks manually is supported:

```bash
uv run pre-commit run --all-files
```

## Notes on ty

- ty is still evolving quickly.
- Configuration lives under `[tool.ty]` in `pyproject.toml`.
- CI and pre-commit run `ty check src`.
