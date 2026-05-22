# EduCoder CLI Solve Path

## Source Files Inspected

- `README.md`
- `src/educoder_cli/cli.py`
- `src/educoder_cli/client.py`
- `.trellis/spec/backend/index.md`

## Command Path

Use these commands from the repository during development:

```bash
uv run educoder status --json
uv run educoder courses --json
uv run educoder homeworks --course <course-id-or-identifier-or-name> --json
uv run educoder task --course <course> --homework <homework-id-or-name> --json
uv run educoder task --course <course> --homework <homework>
uv run educoder code --course <course> --homework <homework> --output <local-file>
uv run educoder submit --course <course> --homework <homework> --file <local-file> --timeout 60 --json
```

## Behavioral Notes

- `status` probes `courses` and returns only authentication/probe metadata in JSON.
- `courses` returns course id, name, identifier, school, and task count.
- `homeworks` returns homework ids/names and challenge progress counts.
- `task` returns the current game, challenge path, rendered statement, test sets, previous/next game identifiers, and last compile output.
- `code` resolves the current context, chooses the challenge path unless `--path` is provided, and writes remote code locally when `--output` is used.
- `submit` reads local code or stdin, saves it remotely, triggers build/evaluation, polls by default, and exits non-zero when evaluation fails.

## Safety Constraints

- Treat `submit` as state changing because it saves code remotely and starts evaluation.
- Do not log or persist credentials, cookies, headers, raw API payloads, or submitted source.
- Use `--json` for machine-readable command output, but summarize only non-secret fields in artifacts.
- If no target course/homework is specified, discover candidates but ask before submitting.

## Real Path Validation

Validated on 2026-05-22 with saved local credentials:

- `uv run educoder status --json` succeeded and confirmed authentication.
- `uv run educoder courses --json` returned accessible courses.
- `uv run educoder homeworks --course W7FXE5NN --json` returned homework rows.
- `uv run educoder task --course W7FXE5NN --homework 2811741 --json` returned a current task with path `Timer24.circ`, rendered statement, test sets, and status `通过`.
- `uv run educoder code --course W7FXE5NN --homework 2811741 --output /tmp/educoder-solve-task-path/Timer24.circ --force --json` wrote a local file successfully.
- The temporary code file was checked for byte size only, then removed.
- `submit` was intentionally not run because it is state changing and no user-selected submission target was provided.
