# Logging Guidelines

> Console output and diagnostics conventions.

---

## Overview

The project does not currently use Python's `logging` module or a structured
logging library. User-visible output is handled at the CLI boundary with Rich:

- `console = Console()` for normal stdout output.
- `err_console = Console(stderr=True)` for errors.
- Rich `Table` for tabular command output.

Library code in `client.py`, `models.py`, and `signature.py` should not print or
log. It should return values or raise exceptions.

---

## Log Levels

There are no project log levels today. Until a real logging layer is introduced:

- Use normal Rich stdout output for requested command results.
- Use Rich stderr output for user-facing command errors.
- Avoid debug output by default; this CLI works with credentials and submitted
  code, so noisy diagnostics can leak sensitive data.

If future verbose diagnostics are added, make them opt-in behind an explicit
Typer option and write them to stderr, not stdout.

---

## Structured Logging

There is no structured log format. Do not add JSON logs or persistent log files
for normal CLI operation.

If structured diagnostics become necessary, define a redaction policy first and
cover it with tests. At minimum, redact:

- `EDUCODER_ZZUD`
- `EDUCODER_AUTOLOGIN`
- `EDUCODER_SESSION`
- `Cookie`
- `Pc-Authorization`
- Submitted source code and Educoder response bodies that may contain code

---

## What to Log

Current commands should output only what the user asked to see.

Examples:

- `version` prints the package version.
- `courses` prints a Rich table with course ID, name, identifier, school, and
  task count.
- Missing credentials and API failures print concise error messages to stderr.

For new commands, render domain results at the CLI boundary and keep client
methods quiet.

---

## What NOT to Log

Never print or log:

- Browser cookie values, auth headers, `zzud`, or session tokens.
- Full request headers.
- Full request or response bodies unless the command explicitly exists to display
  that content.
- Submitted code from `save_code()` or `submit()`.
- Raw exceptions from third-party libraries when they include URLs, headers, or
  payloads.

Also avoid using `print()` in runtime code. The current CLI pattern is Rich
`Console`, and non-CLI modules should remain output-free.

### Credential Persistence Exception

`educoder login` is the only command that may persist credential values. Its
primary result is a saved login state containing the newly issued `EDUCODER_ZZUD`,
`EDUCODER_AUTOLOGIN`, and `EDUCODER_SESSION` equivalents required by the
authenticated CLI workflow.

This exception is narrow:

- It applies only to writing the credential file from the explicit `login`
  command, not errors, debug output, tests with real values, or any other
  command.
- The command must not print the password, saved token values, request body, full
  headers, `Cookie`, or `Pc-Authorization`.
- README examples should prefer password prompting over `--password <value>` so
  users do not put passwords in shell history by default.
