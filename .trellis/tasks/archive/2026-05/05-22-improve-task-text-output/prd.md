# Improve Task Command Text Output

## Goal

Make `educoder task --course ... --homework ...` useful in normal text mode by
including the current challenge problem statement instead of only a short
metadata table.

## What I Already Know

* The user reports that the non-JSON `task` subcommand output is too brief and
  does not include the problem statement.
* `src/educoder_cli/cli.py` owns Typer command definitions and Rich terminal
  rendering.
* `_task_detail_to_dict()` already exposes `task.challenge.task_pass` in JSON
  output, so this task should not require a client/API change.
* `_render_task_detail()` currently renders only homework/challenge metadata,
  optional compile output, and test sets.

## Requirements

* Text-mode `task` output must include the challenge problem statement when
  `TaskDetail.challenge.task_pass` is present.
* JSON output must remain machine-readable and keep the existing shape.
* Rendering must escape Rich markup and avoid leaking credentials, headers,
  submitted source code, or raw request/response payloads.
* Existing test-set rendering behavior must remain intact, including nullable
  fields.

## Acceptance Criteria

* [ ] `educoder task --course py --homework 42` includes the problem statement
      in text mode when the API detail contains one.
* [ ] `educoder task --course py --homework 42 --json` continues to expose the
      existing `task.challenge.task_pass` field.
* [ ] CLI tests cover the text-mode problem statement rendering.
* [ ] Local checks pass: `uv run ruff format --check .`,
      `uv run ruff check .`, `uv run ty check`, and `uv run pytest -q`.

## Definition of Done

* Tests added or updated for the changed behavior.
* Lint, type check, and test suite pass.
* No unrelated refactors or CLI contract changes.
* Trellis finish steps reviewed after implementation.

## Technical Approach

Update the CLI renderer for `TaskDetail` so the summary table remains compact
and the problem statement is rendered as a dedicated readable block before test
sets. Keep this in `cli.py` because terminal formatting belongs at the CLI
boundary.

## Decision (ADR-lite)

**Context**: The data already exists in the parsed model and JSON output, but
the default Rich output omits it.

**Decision**: Reuse `TaskDetail.challenge.task_pass` in text mode and add focused
CLI coverage with the existing fake client.

**Consequences**: This is a narrow output-only change. If Educoder returns HTML
in `task_pass`, the renderer may need light normalization so the terminal output
is readable without adding a new dependency.

## Out of Scope

* Adding new API calls or changing task context resolution.
* Changing `--json` output structure.
* Rendering or printing submitted source code.

## Technical Notes

* Relevant specs read:
  * `.trellis/spec/backend/index.md`
  * `.trellis/spec/backend/cli-command-guidelines.md`
  * `.trellis/spec/backend/directory-structure.md`
  * `.trellis/spec/backend/quality-guidelines.md`
  * `.trellis/spec/backend/logging-guidelines.md`
* Likely changed files:
  * `src/educoder_cli/cli.py`
  * `tests/test_cli.py`
