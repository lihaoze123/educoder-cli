# Error Handling

> How failures are represented, propagated, and surfaced.

---

## Overview

The project keeps error handling split by layer:

- `client.py` converts Educoder protocol failures into custom exceptions or
  raises `ValueError` for missing local workflow context.
- `errors.py` defines the custom exception taxonomy.
- `cli.py` catches `EduCoderAPIError`, prints a red Rich error on stderr, and
  exits with code 1.
- Credential validation in the CLI prints missing environment variable names and
  exits with code 2.

Client code should raise; CLI code should decide how to print and exit.

---

## Error Types

Custom error types live in `src/educoder_cli/errors.py`:

- `EduCoderAPIError`: base class for API/protocol failures; optionally carries
  `status_code`.
- `SessionExpiredError`: raised for HTTP 401 responses.
- `SignatureError`: raised when the Educoder API reports signature failure with
  `status == -102`.
- `EvaluationTimeoutError`: raised when evaluation polling does not complete in
  the configured timeout.

Use these exceptions for remote API and Educoder workflow failures. Use
`ValueError` for invalid local call state, such as missing selected course,
homework, game, or code path. Current examples are in `EduCoderClient` methods
like `get_homeworks()`, `get_task_detail()`, `save_code()`, and
`get_current_context()`.

---

## Error Handling Patterns

### API Request Conversion

`EduCoderClient._request()` is the single place that sends HTTP and normalizes
remote response failures:

```python
if resp.status_code == 401:
    raise SessionExpiredError("Cookie expired, fetch fresh browser cookies", status_code=401)

try:
    data = resp.json()
except (json.JSONDecodeError, ValueError) as exc:
    raise EduCoderAPIError(f"Non-JSON response: {resp.text[:300]}") from exc

if data.get("status") == -102:
    raise SignatureError("Signature verification failed")
```

The source messages are currently Chinese in `client.py`; keep user-facing
messages understandable for the target CLI user. Preserve exception chaining
with `raise ... from exc` when wrapping parser or library errors.

### Local Context Validation

Methods that depend on prior selection should validate early and raise
`ValueError` with a clear message before sending a request. Existing examples:

- `get_homeworks()` requires `course_identifier`.
- `get_task_detail()` requires `game_identifier` and `homework_common_id`.
- `save_code()` and `game_build()` require selected homework/game context.

Do not allow missing state to produce malformed API URLs or request bodies.

### Polling and Workflow Failures

Longer workflows should return structured results on success and raise a custom
exception on timeout or unrecoverable API failure. `submit()` returns a
`JsonObject` containing `task_detail`, `passed`, and `test_sets`; `_poll_result()`
raises `EvaluationTimeoutError` after the timeout.

---

## API Error Responses

This is a CLI package, not an HTTP server, so there is no local API error
response schema. CLI commands should convert errors to terminal output:

- Missing credentials: print missing `EDUCODER_*` variables to stderr and raise
  `typer.Exit(2)`.
- Educoder API failures: catch `EduCoderAPIError`, escape the message with
  `rich.markup.escape()`, print to `err_console`, then raise `typer.Exit(1)`.

Reference: `src/educoder_cli/cli.py` implements `_require_credentials()` and
`_print_error()` with this pattern.

---

## Common Mistakes

- Do not print from `client.py`; raise exceptions and let the CLI boundary render
  terminal output.
- Do not catch broad `Exception` in CLI commands unless the command converts it
  into a deliberate user-facing exit behavior.
- Do not expose raw response bodies beyond the short non-JSON preview already
  used in `_request()`.
- Do not include cookies, session values, request headers, submitted code, or
  full Educoder payloads in exception messages.
- Do not duplicate HTTP status/signature handling in individual endpoint methods;
  keep it centralized in `_request()`.
