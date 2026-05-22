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
