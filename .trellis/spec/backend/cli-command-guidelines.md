# CLI Command Guidelines

> Executable contracts for Typer/Rich commands in `educoder-cli`.

## Scenario: Educoder Workflow Commands

### 1. Scope / Trigger

Use this contract when adding or changing a user-facing Typer command in
`src/educoder_cli/cli.py`, especially commands that select a course/homework,
read remote code, or submit source code.

### 2. Signatures

Supported workflow commands use flat top-level Typer commands:

```bash
educoder courses [--page N] [--limit N] [--json]
educoder login --login <username|phone|email> [--password <password>] [--json]
educoder status [--json]
educoder homeworks --course <id|identifier|name> [--json]
educoder task --course <id|identifier|name> --homework <id|name> [--json]
educoder code --course <id|identifier|name> --homework <id|name> [--path <remote>] [--output <file> --force] [--json]
educoder submit --course <id|identifier|name> --homework <id|name> --file <file|-> [--no-wait] [--timeout N] [--poll-interval N] [--json]
```

All authenticated commands keep the existing credential options and env vars:

```bash
--zzud          EDUCODER_ZZUD
--autologin     EDUCODER_AUTOLOGIN
--session       EDUCODER_SESSION
```

`login` is the credential-bootstrap command. It does not require existing
`EDUCODER_*` values. It persists the returned login state for later commands.
Prefer prompting for the password when `--password` is omitted so the README path
does not put passwords in shell history.

### 3. Contracts

- CLI commands remain thin: parse options, validate local file/stdin behavior,
  call `EduCoderClient`, then render terminal output.
- Endpoint URLs, request signing, query strings, request bodies, and polling
  mechanics stay in `client.py`.
- `login` delegates the login endpoint, request body, cookie extraction, and
  API-status interpretation to `EduCoderClient.login()`.
- `login` saves newly issued `EDUCODER_ZZUD`, `EDUCODER_AUTOLOGIN`, and
  `EDUCODER_SESSION` equivalents through the credential persistence helper; do
  not print the password, request body, full headers, or credential values.
- Authenticated commands resolve credentials in this priority order: explicit
  options, environment variables, saved login state.
- `status` validates credentials through a lightweight client call and must not
  implement a separate endpoint, signing path, or alias command.
- Course selectors support ID, exact identifier, exact name, then name fragment.
- Homework selectors support ID, exact name, then name fragment.
- Multiple selector matches must raise a local error and show candidates; never
  silently pick the first match.
- `--json` output must be machine-readable JSON without Rich ANSI highlighting.
- Text-mode `task` output renders the task summary plus the current challenge
  problem statement from `TaskDetail.challenge.task_pass` when present. Normalize
  common HTML markup at the CLI rendering boundary for terminal readability, but
  keep `--json` output as the stable machine-readable model data.
- `code` may display remote source code because that is the explicit command
  result; `submit` must not print submitted source code.
- `submit --file -` reads source from stdin.
- `submit --timeout` must be passed to the client polling workflow.

### 4. Validation & Error Matrix

| Condition | Expected CLI behavior |
|-----------|-----------------------|
| Missing credential options/env/saved login state | Print missing `EDUCODER_*` names to stderr and exit `2` |
| Saved login state is corrupt or incomplete | Print escaped local error to stderr and exit `1` |
| Missing `login --login` option | Let Typer report usage and exit `2` |
| Missing `login --password` option | Prompt securely; empty/aborted input must not send a login request |
| Login API reports invalid credentials or account binding failure | Print escaped error message to stderr and exit `1` |
| Login response lacks required session cookies | Print escaped error message to stderr and exit `1` |
| Login succeeds but credential file cannot be written | Print escaped local error to stderr and exit `1` |
| `status` credentials are valid | Print authenticated status or JSON and exit `0` |
| `status` credentials are missing after saved-state fallback | Print missing `EDUCODER_*` names to stderr and exit `2` |
| `status` API/session validation fails | Print escaped error message to stderr and exit `1` |
| API/protocol error | Print escaped error message to stderr and exit `1` |
| Missing local context, course, homework, or file | Print escaped error message to stderr and exit `1` |
| Multiple course/homework matches | Print error plus candidate table to stderr and exit `1` |
| `code --output` target exists without `--force` | Refuse overwrite and exit `1` |
| `submit` evaluation passes | Exit `0` |
| `submit` evaluation fails or times out | Exit `1` |
| `submit --no-wait` submission is accepted | Exit `0` |

### 5. Good/Base/Bad Cases

- Good: `submit` reads a local file, selects course/homework through the client,
  passes `timeout` and `poll_interval`, renders test results, and exits according
  to evaluation status.
- Good: `login` prompts for a password when omitted, sends the login workflow
  through the client, stores only the returned token values, and prints a short
  success message without secrets.
- Good: `status` calls an existing lightweight authenticated client method such
  as `get_courses(page=1, limit=1)` and renders only success/failure metadata.
- Good: `courses` with no env/options uses saved login state when available.
- Base: `homeworks --json` returns selected course metadata and a stable list of
  homework summaries without raw API payloads.
- Bad: a CLI command builds an Educoder endpoint URL directly or prints submitted
  source code while reporting a submission error.
- Bad: adding `check` or `check-health` as aliases when the accepted command
  contract is only `status`.

### 6. Tests Required

- CLI commands should be tested with Typer `CliRunner` and a fake
  `EduCoderClient`; do not hit the real Educoder network.
- Cover JSON output, default Rich/stdout output, credential failure, API failure,
  file overwrite refusal, stdin reading, `--no-wait`, and non-zero failed
  evaluation exits.
- `task` text-output tests should assert the problem statement renders when
  `challenge.task_pass` is present and should cover HTML-to-text normalization
  without changing the `--json` payload shape.
- Login tests should assert request delegation and save delegation via fakes at
  the CLI layer, and cookie/header/body behavior through `httpx.MockTransport`
  at the client layer.
- Credential persistence tests should assert path selection, JSON round trip,
  missing-file behavior, invalid-file errors, and restrictive file permissions
  on POSIX platforms.
- Status tests should assert the command uses credential options/env vars, probes
  with `page=1` and `limit=1`, falls back to saved login state, exits `2` on
  missing credentials, and exits `1` on API/session errors.
- Client selector behavior should have focused tests for ambiguous matches.
- Polling option changes should assert that CLI/client options reach the polling
  boundary.

### 7. Wrong vs Correct

#### Wrong

```python
@app.command()
def submit(...):
    url = f"https://data.educoder.net/api/tasks/{game}/game_build.json"
    httpx.post(url, json={...})
```

This duplicates signing, auth, URL construction, and API error handling in the
CLI layer.

#### Correct

```python
@app.command()
def submit(...):
    with EduCoderClient(*auth) as client:
        client.select_course(course)
        client.select_homework(homework)
        result = client.submit(source, timeout=timeout)
```

The CLI selects context, delegates workflow behavior to the client, and renders
the result.

## Scenario: Shixun Homework Task Context Resolution

### 1. Scope / Trigger

Use this contract when changing how `task`, `code`, or `submit` resolve the
selected shixun homework into a task `game_identifier`.

### 2. Signatures

Client methods own the resolution flow:

```python
EduCoderClient.select_homework(identifier, *, course_identifier=None)
EduCoderClient.get_current_context()
EduCoderClient.get_shixun_exec(shixun_identifier=None, homework_common_id=None)
```

Current Educoder launch API:

```text
GET /api/shixuns/{shixun_identifier}/shixun_exec.json?homework_common_id={id}&zzud={zzud}
```

### 3. Contracts

- `select_homework()` sets `homework_common_id`, `shixun_identifier`,
  `myshixun_identifier`, and a fresh `game_identifier` for the selected homework.
- When switching homework on the same client instance, reset any previous
  `game_identifier` before resolving the new selection.
- Prefer existing `myshixun_identifier` resolution when it returns
  `game_identifier`, but fall back to `shixun_exec` because the legacy
  `/myshixuns/{id}.json` endpoint may return a 404 JSON payload.
- `shixun_exec` success is a loose JSON object containing `game_identifier`.
  Keep it typed as `JsonObject`; do not add a dataclass unless the response
  shape becomes stable and broader than this field.
- CLI commands must not build this endpoint directly.

### 4. Validation & Error Matrix

| Condition | Expected behavior |
|-----------|-------------------|
| No selected/explicit `shixun_identifier` | `get_shixun_exec()` raises `ValueError("请先指定 shixun_identifier")` |
| No selected/explicit `homework_common_id` | `get_shixun_exec()` raises `ValueError("请先指定 homework_common_id")` |
| Legacy myshixun lookup returns no `game_identifier` | Try `shixun_exec` before failing |
| Both resolution paths return no `game_identifier` | `get_current_context()` raises the existing missing-game `ValueError` |
| Remote auth/signature/network failure | Let `_request()` convert or propagate the existing `EduCoderAPIError` family |

### 5. Good/Base/Bad Cases

- Good: `task --course X --homework Y` selects the homework, resolves
  `game_identifier` through the client, then calls `get_task_detail()`.
- Base: a stale `/myshixuns/{id}.json` response with `status: 404` is treated as
  "no game id here" and falls through to `shixun_exec`.
- Bad: reusing a previous homework's `game_identifier` after
  `select_homework()` is called again.
- Bad: duplicating the `shixun_exec` URL in `cli.py` or tests that fake the CLI
  instead of testing `EduCoderClient`.

### 6. Tests Required

- Client test with `httpx.MockTransport` where `/myshixuns/{id}.json` returns
  a stale 404 JSON payload and `shixun_exec` returns `game_identifier`.
- Client test that selecting homework A then homework B on the same client
  updates `game_identifier` to homework B's value.
- CLI tests can keep using a fake client; endpoint details belong in
  `tests/test_client.py`.

### 7. Wrong vs Correct

#### Wrong

```python
def select_homework(...):
    # Leaves a previous task context in place when the next homework is selected.
    if self.game_identifier:
        return target
```

#### Correct

```python
def select_homework(...):
    self.homework_common_id = target.homework_id
    self.shixun_identifier = target.shixun_identifier
    self.myshixun_identifier = target.myshixun_identifier
    self.game_identifier = None
    self._resolve_game_identifier()
```

## Scenario: Nullable Test Set Execution Fields

### 1. Scope / Trigger

Use this contract when changing `TaskDetail`, `TestSet`, `task`, `code`, or
`submit` rendering/output around Educoder test-set data.

### 2. Signatures

Educoder task detail responses may include test-set entries like:

```json
{
  "result": null,
  "output": "expected output",
  "actual_output": null,
  "compile_success": null,
  "is_public": true,
  "ts_time": null,
  "ts_mem": null
}
```

The local model must allow nullable execution fields:

```python
TestSet.result: bool | None
TestSet.output: str | None
TestSet.actual_output: str | None
TestSet.compile_success: int | None
TestSet.ts_time: float | None
TestSet.ts_mem: float | None
```

### 3. Contracts

- Preserve `None` for API fields whose meaning is "not evaluated yet" or
  "unknown"; do not coerce them to failure, zero, or the literal string
  `"None"`.
- Text-mode Rich tables render nullable cells as blank strings.
- JSON output preserves `None` as JSON `null` for machine consumers.
- Keep this normalization at model/render boundaries. Do not catch broad
  exceptions around rendering to hide payload contract bugs.

### 4. Validation & Error Matrix

| Condition | Expected behavior |
|-----------|-------------------|
| `actual_output` is `null` | Text rendering shows a blank Actual cell and exits `0` |
| `result` is `null` | Text rendering shows a blank Result cell, not `fail` |
| `ts_time` or `ts_mem` is `null` | Text rendering shows blank Time/Memory cells |
| `output` is present | Expected output is still rendered and truncated safely |
| `--json` output requested | Nullable fields remain `null` in JSON |

### 5. Good/Base/Bad Cases

- Good: an unstarted task with expected output but no actual output displays the
  task table and test-set table without traceback.
- Base: a completed test set with boolean result and numeric runtime keeps the
  existing `pass`/`fail`, time, memory, expected, and actual output display.
- Bad: passing nullable fields directly to helpers that call `len()` or other
  string-only operations.
- Bad: converting `None` result to `False`, which incorrectly labels an
  unstarted case as failed.

### 6. Tests Required

- Model parser test proving nullable test-set execution fields remain `None`.
- CLI text rendering test proving `actual_output=None`, `result=None`,
  `ts_time=None`, and `ts_mem=None` do not crash and render the expected output.
- Keep CLI tests on fake clients; live Educoder checks can verify manually but
  must not be required in the test suite.

### 7. Wrong vs Correct

#### Wrong

```python
escape(_truncate(test_set.actual_output, 120))
str(test_set.ts_time)
"pass" if test_set.result else "fail"
```

This crashes on `actual_output=None`, prints `"None"` for runtime fields, and
mislabels unknown results as failures.

#### Correct

```python
_test_result_label(test_set.result)
_format_optional(test_set.ts_time)
escape(_truncate(test_set.actual_output, 120))
```
