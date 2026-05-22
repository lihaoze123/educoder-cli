# Quality Guidelines

> Code quality standards for this Python CLI package.

---

## Overview

The repository uses:

- `uv` for environment and dependency management.
- `ruff` for formatting and linting.
- `ty` for type checking.
- `pytest` for tests.
- Python 3.13 and modern type syntax.

The authoritative tool configuration is in `pyproject.toml`. The local quality
commands are listed in `README.md`:

```bash
uv run ruff format --check .
uv run ruff check .
uv run ty check
uv run pytest -q
```

Ruff intentionally excludes generated Trellis/agent integration directories
(`.agents`, `.claude`, `.codex`, `.trellis`) so the app checks focus on project
source and tests rather than scaffolding maintained by Trellis.

## Scenario: Quality Tooling Contract

### 1. Scope / Trigger

Use this contract whenever a change touches Python source, tests, package
metadata, tooling configuration, or Trellis specs that claim local checks pass.

### 2. Signatures

Run these commands from the repository root:

```bash
uv run ruff format --check .
uv run ruff check .
uv run ty check
uv run pytest -q
```

### 3. Contracts

- `pyproject.toml` is the source of truth for tool configuration.
- Ruff checks `src`, `tests`, and root Python entry points, while excluding
  generated integration scaffolding: `.agents`, `.claude`, `.codex`, `.trellis`.
- `ty` checks `src` and `tests` with Python 3.13 settings.
- pytest discovers tests from `tests/` with `pythonpath = ["src"]`.

### 4. Validation & Error Matrix

| Condition | Expected response |
|-----------|-------------------|
| Ruff format check fails on app code | Run `uv run ruff format .`, inspect the diff, then rerun checks |
| Ruff lint fails on app code | Fix the lint finding or document a narrow, justified ignore |
| Ruff fails only on generated Trellis/agent scaffolding | Adjust the tooling exclusion if needed; do not rewrite generated files by hand |
| `ty check` fails | Fix annotations/contracts rather than hiding errors with broad `Any` |
| pytest fails | Fix the regression or update tests only when behavior intentionally changed |

### 5. Good/Base/Bad Cases

- Good: a new client method has typed parameters, uses `_get()` or `_post()`,
  includes `httpx.MockTransport` tests, and all four commands pass.
- Base: a docs-only spec change runs the same commands and confirms no template
  markers remain.
- Bad: a change reports success after running only pytest, or edits generated
  Trellis hook files just to satisfy Ruff.

### 6. Tests Required

- New source behavior needs focused pytest coverage in the matching
  `tests/test_<module>.py` file.
- New API request behavior should assert endpoint/query/header details through
  `httpx.MockTransport`.
- New parser defaults should assert both required fields and defaulted optional
  fields.
- Tooling configuration changes should be verified by rerunning all four local
  check commands.

### 7. Wrong vs Correct

#### Wrong

```bash
uv run pytest -q
```

Reporting green after only the test suite misses formatting, lint, and type
contract drift.

#### Correct

```bash
uv run ruff format --check .
uv run ruff check .
uv run ty check
uv run pytest -q
```

Run the full suite and treat generated Trellis/agent files as excluded tooling
artifacts, not application code to hand-format.

---

## Forbidden Patterns

- Do not bypass `EduCoderClient._request()` for API calls. Direct `httpx` calls
  outside `client.py` duplicate signing, cookies, JSON validation, and API error
  conversion.
- Do not put terminal rendering in `client.py` or `models.py`; keep Rich output
  in `cli.py`.
- Do not put endpoint URLs or Educoder query-string construction in CLI commands.
- Do not mutate dataclass parser input dictionaries; `from_dict()` constructors
  should read mappings and return new model instances.
- Do not add untyped helper functions. The project uses explicit annotations and
  `ty check`.
- Do not introduce persistent storage, local caches, or log files without a
  separate design task.
- Do not print or log credentials, headers, submitted code, or raw API payloads.

---

## Required Patterns

- Use `typing.Annotated` for Typer options, as in `cli.py`.
- Use `httpx.Client` injection for testable API code. Tests should be able to pass
  `httpx.MockTransport` through the client constructor.
- Use context management for owned clients: `with EduCoderClient(*auth) as client`.
- Use dataclasses plus `from_dict()` for stable Educoder response models.
- Default optional model fields in dataclasses to safe empty values, using
  `field(default_factory=list)` for lists.
- Normalize Educoder path values with the existing full-width/ASCII semicolon
  trimming pattern where API paths are consumed.
- Keep public package exports in `src/educoder_cli/__init__.py` intentional.
- Use `JsonObject = dict[str, Any]` for loose JSON payloads in `client.py`.

---

## Testing Requirements

Use focused pytest tests that mirror the module under change:

- Client API behavior belongs in `tests/test_client.py`.
- Model parser/default behavior belongs in `tests/test_models.py`.
- Signature behavior belongs in `tests/test_signature.py`.
- New modules should get matching `tests/test_<module>.py` files.

For HTTP behavior, use `httpx.MockTransport` rather than live Educoder calls.
Current client tests assert both parsed results and request side effects such as
query params and auth headers.

For parser tests, include minimal API dictionaries and assert defaults. Current
tests verify `Course.from_dict()`, `HomeworkCommon.from_dict()`, and nested
`TaskDetail.from_dict()` behavior.

For time-dependent signing code, monkeypatch time instead of sleeping or relying
on wall-clock values.

---

## Code Review Checklist

- Does the change belong in the right layer: CLI, client, model, error, signature,
  or test?
- Are API calls routed through `_get()`/`_post()` and `_request()`?
- Are Educoder credentials and submitted code kept out of output, logs, and error
  strings?
- Are user-facing CLI errors printed on stderr with a deliberate exit code?
- Are stable response shapes modeled with dataclasses and tested for defaults?
- Are loose payloads typed as `JsonObject` rather than unbounded `Any` flowing
  through public APIs?
- Do tests avoid network access and cover request headers/query params where the
  endpoint behavior depends on them?
- Do all local checks pass: `ruff format --check`, `ruff check`, `ty check`, and
  `pytest -q`?
