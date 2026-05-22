# Support Login and Health Commands

## Goal

Add first-class CLI support for logging into EduCoder with username/phone/email
and password, persist the resulting login state locally, and add a lightweight
authenticated status check so users can verify whether their current credentials
are usable.

## What I Already Know

- The user asked to support a `login` subcommand.
- The user asked to add a health command and later clarified that only `status`
  should be implemented.
- The login API details are documented in
  `temp-阅后删除-educoder_login_research.md`.
- Current authenticated commands accept `EDUCODER_ZZUD`, `EDUCODER_AUTOLOGIN`,
  and `EDUCODER_SESSION`, or matching CLI options.
- The user clarified that login state should be persisted.
- Existing CLI commands are flat top-level Typer commands with `--json` support
  when structured output is useful.

## Requirements

- Add `educoder login` to call the documented EduCoder login API.
- Accept account identifier and password as CLI inputs without hardcoding or
  prompting from the client layer.
- Reuse the existing Educoder signing implementation.
- Convert login API failures into existing custom API errors and CLI exit
  behavior.
- Extract `_educoder_session` and `autologin_trustie` from response cookies.
- Persist the resulting `zzud`, `autologin_trustie`, and `_educoder_session`
  values locally for future authenticated commands.
- Do not persist the account password.
- Authenticated commands should resolve credentials in this priority order:
  explicit options, environment variables, saved login state.
- Add `educoder status` to validate current credentials through
  `EduCoderClient`.
- Add focused client and CLI tests using `httpx.MockTransport` and Typer
  `CliRunner`; tests must not hit the live Educoder network.
- Update README CLI usage examples.

## Acceptance Criteria

- [x] `educoder login --login <account> --password <password>` succeeds against a
  mocked login response and persists the values needed by existing authenticated
  commands.
- [x] Login handles documented negative API statuses with user-facing errors and
  exit code `1`.
- [x] Login requires missing local inputs at the Typer boundary and does not
  silently send empty credentials.
- [x] `educoder status` exits `0` using saved login state when no explicit
  credentials are provided.
- [x] Existing authenticated commands use saved login state when no explicit
  credentials are provided.
- [x] `educoder status` exits `0` when credentials can fetch a lightweight
  authenticated resource.
- [x] `educoder status` exits `2` on missing credentials and `1` on API or
  session failures.
- [x] JSON output is machine-readable and not Rich-highlighted.
- [x] Full local quality checks pass.

## Definition of Done

- Tests added or updated for client and CLI behavior.
- `uv run ruff format --check .`, `uv run ruff check .`, `uv run ty check`, and
  `uv run pytest -q` pass.
- README documents the new login and status/check command.
- Temporary login research document is no longer needed by implementation.

## Technical Approach

- Keep endpoint construction, request body, response parsing, cookie extraction,
  and API error conversion in `src/educoder_cli/client.py`.
- Keep command parsing, password prompting option, credential persistence
  orchestration, JSON rendering, and exit codes in `src/educoder_cli/cli.py`.
- Add a small local credential persistence module that stores the login result as
  JSON under the user config directory with restrictive permissions.
- Add a small login result dataclass in `models.py` if the parsed response shape
  is stable enough; otherwise return a typed `JsonObject` from the client. A
  dataclass is preferred for testability and CLI rendering.
- Implement `status` by reusing `get_courses(page=1, limit=1)` as the
  lowest-risk authenticated probe currently available.

## Out of Scope

- Persisting passwords, submitted code, request bodies, raw headers, or full API
  payloads.
- Adding keyring integration, dotenv files, shell profile modification, or a
  database.
- Automatic session refresh using stored username/password.
- Browser-based login, captcha handling, or MFA flows.
- `check` and `check-health` command aliases.
- Any live-network integration tests.

## Research References

- [`research/login-api.md`](research/login-api.md) - summarized login endpoint,
  cookie behavior, and repo mapping from the temporary API document.

## Technical Notes

- Relevant specs:
  - `.trellis/spec/backend/index.md`
  - `.trellis/spec/backend/cli-command-guidelines.md`
  - `.trellis/spec/backend/error-handling.md`
  - `.trellis/spec/backend/database-guidelines.md`
  - `.trellis/spec/backend/quality-guidelines.md`
- Relevant code:
  - `src/educoder_cli/cli.py`
  - `src/educoder_cli/client.py`
  - `src/educoder_cli/models.py`
  - `src/educoder_cli/signature.py`
  - `tests/test_cli.py`
  - `tests/test_client.py`
