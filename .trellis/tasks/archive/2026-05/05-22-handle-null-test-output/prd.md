# Handle Null Test Output Rendering

## Goal

Prevent `educoder task` from crashing when Educoder returns `null` for optional
test-set fields such as `actual_output`, `ts_time`, or `ts_mem`.

## Requirements

* Render nullable test-set values as blank strings in Rich tables.
* Preserve existing task-detail and test-set output formatting for non-null
  values.
* Add regression coverage for `educoder task --json` and/or text rendering paths
  where test-set output fields are `None`.
* Do not print raw API payloads, credentials, or submitted code.

## Acceptance Criteria

* [x] `educoder task --course 112258 --homework 3635136` exits cleanly in text
      mode after showing task and test-set data.
* [x] A test covers rendering test sets with `actual_output=None`.
* [x] Lint, type check, and tests pass.

## Definition of Done

* Focused test coverage added for the crash.
* `uv run ruff format --check .`, `uv run ruff check .`, `uv run ty check`, and
  `uv run pytest -q` pass.
* Spec update considered after implementation.

## Technical Approach

Keep the fix at the CLI rendering boundary. `_truncate()` currently accepts only
`str`; either make the caller normalize optional values before truncating, or
make `_truncate()` tolerate `None` consistently for all rendered nullable fields.

## Out of Scope

* Changing Educoder API parsing for all fields.
* Reworking task-detail layout.
* Modifying submission/evaluation behavior.

## Technical Notes

* The traceback points to `src/educoder_cli/cli.py::_render_test_sets()`, where
  `test_set.actual_output` can be `None`.
* `tests/test_cli.py` already has text-mode command tests using a fake client.
