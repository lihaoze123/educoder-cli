# educoder-cli Command Reference

## Install The CLI

Install `uv` first if it is not available. Then install the released CLI from this repository:

```bash
uv tool install git+https://github.com/lihaoze123/educoder-cli
educoder --help
```

From a local clone of this repository, run commands through the development environment instead:

```bash
uv sync --all-extras --dev
uv run educoder --help
```

Log in once before solving homework:

```bash
educoder login --login <account>
educoder status --json
```

Use environment variables only when the user already has them configured:

```bash
EDUCODER_ZZUD=... EDUCODER_AUTOLOGIN=... EDUCODER_SESSION=... educoder status --json
```

Do not ask the user to paste credential values into chat.

## Commands

Use `educoder` after tool installation. Use `uv run educoder` from the repository root.

```bash
educoder status --json
educoder courses --json
educoder homeworks --course <course-id-or-identifier-or-name> --json
educoder task --course <course> --homework <homework-id-or-name> --json
educoder task --course <course> --homework <homework>
educoder code --course <course> --homework <homework> --output <local-file> --force --json
educoder submit --course <course> --homework <homework> --file <local-file> --timeout 60 --json
```

## Selector Rules

- Course selectors accept ID, exact identifier, exact name, then name fragment.
- Homework selectors accept ID, exact name, then name fragment.
- Ambiguous matches are local errors; ask the user to choose a candidate.

## Useful JSON Fields

- `course.identifier`: stable course selector when present.
- `homework.homework_id`: stable homework selector.
- `homework.shixun_identifier` and `homework.myshixun_identifier`: remote shixun context.
- `task.challenge.path`: remote answer file path used by `code` and `submit`.
- `task.challenge.task_pass`: problem statement source.
- `task.last_compile_output`: most recent compile feedback.
- `task.game.status_text`: human-readable pass/fail/current status.
- `task.test_sets[].output`: expected output.
- `task.test_sets[].actual_output`: actual output after evaluation.
- `task.test_sets[].compile_success`: compile result flag when available.

## Observed Real Path

Validated on 2026-05-22 with saved local credentials:

```bash
uv run educoder status --json
uv run educoder courses --json
uv run educoder homeworks --course W7FXE5NN --json
uv run educoder task --course W7FXE5NN --homework 2811741 --json
uv run educoder code --course W7FXE5NN --homework 2811741 --output /tmp/educoder-cli-path/Timer24.circ --force --json
```

The task call returned a real challenge with remote path `Timer24.circ`, status `passed`, test-set data, and prior compile output. The code command wrote a local file successfully; the temporary file was removed after checking that it existed. `submit` was not run because it is remote state changing and no user-selected submission target was provided for the skill-building task.

## Exit Behavior

- Missing credentials exit with code 2.
- API, context, overwrite, and evaluation failures exit with code 1.
- `submit --no-wait` exits 0 when the submission is accepted.
- A waited `submit` exits 0 only when evaluation passes.
