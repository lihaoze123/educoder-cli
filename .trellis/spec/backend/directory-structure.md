# Directory Structure

> How the Python CLI package is organized.

---

## Overview

This is a single-package Python project using the `src/` layout. Keep runtime
code under `src/educoder_cli/`, tests under `tests/`, and project/tooling
configuration in `pyproject.toml`.

The source layout is deliberately flat because the package is small. Add a new
module only when it has a clear ownership boundary comparable to the existing
`client`, `models`, `errors`, and `signature` modules.

---

## Directory Layout

```
.
├── main.py                       # local script entry point, delegates to the Typer app
├── pyproject.toml                # package metadata and ruff/pytest/ty config
├── src/
│   └── educoder_cli/
│       ├── __init__.py           # public package exports and version
│       ├── __main__.py           # python -m educoder_cli entry point
│       ├── cli.py                # Typer commands and Rich terminal output
│       ├── client.py             # sync HTTP client and Educoder workflow methods
│       ├── errors.py             # custom API exception types
│       ├── models.py             # dataclass response models and parsing
│       └── signature.py          # Educoder request signature generation
└── tests/
    ├── test_client.py
    ├── test_models.py
    └── test_signature.py
```

---

## Module Organization

### CLI Boundary

Add user-facing commands in `src/educoder_cli/cli.py`. The local pattern is:

- Declare reusable Typer option aliases with `typing.Annotated`.
- Read authentication from explicit options and environment variables.
- Use Rich `Console`/`Table` for terminal output.
- Keep CLI functions thin: validate inputs, call `EduCoderClient`, render results.

Reference: `cli.py` defines `ZzudOption`, `AutologinOption`, and `SessionOption`
once, then reuses them in the `courses` command.

```python
ZzudOption = Annotated[
    str | None,
    typer.Option("--zzud", envvar="EDUCODER_ZZUD", help="Educoder zzud value."),
]
```

### API Client Layer

Put Educoder HTTP behavior in `src/educoder_cli/client.py` on `EduCoderClient`.
Follow the existing split:

- `_headers()` builds signed headers.
- `_request()` sends HTTP, parses JSON, and converts API protocol errors.
- `_get()` and `_post()` are the only method-specific request wrappers.
- Public methods such as `get_courses()`, `save_code()`, and `submit()` compose
  endpoint-specific logic.

Use the existing synchronous `httpx.Client` dependency injection pattern for
testability:

```python
def __init__(..., http_client: httpx.Client | None = None) -> None:
    self._client = http_client or httpx.Client(timeout=30)
    self._owns_client = http_client is None
```

### Model Layer

Put stable API response shapes in `src/educoder_cli/models.py` as dataclasses
with `from_dict()` constructors accepting `Mapping[str, Any]`. Required fields
that are truly required by the API may index directly, while optional fields
should use defaults that match current code.

Reference: `Course.from_dict()` requires `id` but defaults missing metadata;
`TaskDetail.from_dict()` converts nested `game`, `challenge`, `user`, test sets,
and environments.

### Script Entrypoints

Keep entry points as delegators. `main.py` and `src/educoder_cli/__main__.py`
both import the Typer app and call it; they should not contain business logic.

---

## Naming Conventions

- Module files use lowercase snake_case.
- Public client methods use verb-oriented names matching Educoder workflows:
  `get_courses`, `select_homework`, `submit_all_levels`.
- Dataclass model names use Educoder domain nouns: `Course`, `HomeworkCommon`,
  `TaskDetail`, `ShixunEnvironment`.
- Tests use `test_<module>.py` and behavior-focused test names.
- CLI environment variables use the `EDUCODER_` prefix.

---

## Examples

Use these files as reference patterns:

- `src/educoder_cli/cli.py`: Typer command registration, reusable credential
  options, Rich output, and API error-to-exit conversion.
- `src/educoder_cli/client.py`: context-managed sync `httpx` client, signed
  request headers, API response parsing, and multi-step submit workflow.
- `src/educoder_cli/models.py`: dataclass models with explicit parsing defaults.
- `tests/test_client.py`: `httpx.MockTransport` tests for request headers and
  API error conversion.
- `tests/test_models.py`: parser/default behavior tests for dataclasses.

Avoid spreading endpoint URLs or request signing outside `client.py`, and avoid
putting terminal rendering inside model or client methods.
