# Render Task Description as Markdown

## Goal

Improve `educoder task` text output so the problem statement is rendered as
Markdown instead of displaying Markdown source markers such as `###`, `---`, and
`[TOC]` as plain text.

## What I Already Know

* The previous change added the problem statement to text-mode task output.
* The screenshot shows the API-provided statement is Markdown-like text, not
  only HTML.
* `src/educoder_cli/cli.py` currently wraps the statement in a Rich `Panel` after
  escaping it as plain text.
* Rich is already a runtime dependency and provides Markdown rendering.

## Requirements

* Text-mode `task` output must render the problem statement with Rich Markdown.
* Unsupported Educoder table-of-contents marker lines such as `[TOC]` should not
  be shown in CLI output.
* Existing HTML-to-text normalization should keep working for older or mixed
  problem statement payloads.
* JSON output shape must remain unchanged.
* The implementation must stay in the CLI rendering layer and must not add API
  calls, persistence, or new dependencies.

## Acceptance Criteria

* [ ] `educoder task --course ... --homework ...` renders headings/lists/rules
      as Markdown in the task description panel.
* [ ] Literal Markdown source markers such as `###` and `[TOC]` are not shown for
      normal problem statements.
* [ ] Existing HTML statement rendering remains readable.
* [ ] CLI regression tests cover Markdown rendering behavior.
* [ ] Local checks pass: `uv run ruff format --check .`,
      `uv run ruff check .`, `uv run ty check`, and `uv run pytest -q`.

## Definition of Done

* Tests added or updated for changed behavior.
* Lint, type check, and test suite pass.
* Spec guidance updated if the CLI output contract changes.
* Changes committed before finish-work.

## Technical Approach

Use `rich.markdown.Markdown` as the renderable inside the existing
`Task Description` panel. Keep `_format_problem_statement()` responsible for
HTML normalization and light cleanup, including removal of standalone `[TOC]`
markers.

## Decision (ADR-lite)

**Context**: The statement body can contain Markdown syntax. Escaping the whole
body prevents Rich from rendering it and makes the default text output look like
source markup.

**Decision**: Render the normalized statement with Rich Markdown at the CLI
boundary.

**Consequences**: Output becomes more readable in terminals. Markdown rendering
remains an output-only behavior and does not affect the stable JSON payload.

## Out of Scope

* Full Educoder web renderer parity.
* Adding a Markdown extension engine for `[TOC]`.
* Changing task selection, client parsing, or JSON output.

## Technical Notes

* Relevant files:
  * `src/educoder_cli/cli.py`
  * `tests/test_cli.py`
  * `.trellis/spec/backend/cli-command-guidelines.md`
