# Backend Development Guidelines

> Project-specific backend and CLI conventions for `educoder-cli`.

---

## Overview

This repository is a Python 3.13 CLI package for Educoder API workflows. The
runtime shape is intentionally small:

- `src/educoder_cli/cli.py` owns Typer command definitions and Rich terminal output.
- `src/educoder_cli/client.py` owns synchronous HTTP calls, Educoder request signing,
  authenticated request state, and higher-level API workflows.
- `src/educoder_cli/models.py` owns dataclass response models and API payload parsing.
- `src/educoder_cli/errors.py` owns custom API exception types.
- `src/educoder_cli/signature.py` owns Educoder signature generation.
- `tests/` mirrors the source modules with focused pytest coverage.

Before changing backend code, read the relevant guide below and prefer the
patterns already demonstrated in source and tests.

---

## Guidelines Index

| Guide | Description |
|-------|-------------|
| [Directory Structure](./directory-structure.md) | Source layout, module ownership, command/client/model boundaries |
| [Database Guidelines](./database-guidelines.md) | Current no-database stance and persistence rules |
| [Error Handling](./error-handling.md) | Exception taxonomy, API error conversion, CLI exit behavior |
| [Quality Guidelines](./quality-guidelines.md) | Tooling, tests, typing, review expectations |
| [Logging Guidelines](./logging-guidelines.md) | Current console-output pattern and future diagnostics constraints |

## Pre-Development Checklist

- Identify whether the change belongs at the CLI boundary, API client layer, model
  layer, signing helper, or tests.
- Search for an existing helper or pattern before adding a new abstraction.
- Keep authentication cookies, `zzud`, `_educoder_session`, request bodies, and
  submitted code out of logs and error messages.
- For new API responses with stable shape, add or extend dataclasses in
  `models.py`; for loose Educoder payloads, keep the existing `JsonObject` pattern.
- Run the local checks from `README.md`: `uv run ruff format --check .`,
  `uv run ruff check .`, `uv run ty check`, and `uv run pytest -q`.

## Quality Check Checklist

- Confirm changed code stays in the correct layer described by
  [Directory Structure](./directory-structure.md).
- Confirm no change introduces local persistence unless
  [Database Guidelines](./database-guidelines.md) has first been updated with a
  deliberate storage design.
- Confirm remote API failures, local context errors, and CLI exit behavior follow
  [Error Handling](./error-handling.md).
- Confirm output or diagnostics do not expose credentials, headers, request
  bodies, submitted code, or raw Educoder payloads; see
  [Logging Guidelines](./logging-guidelines.md).
- Confirm tests and local checks follow
  [Quality Guidelines](./quality-guidelines.md).
