# Fix Task Game Identifier Resolution

## Goal

Make `educoder task --course ... --homework ...` work for shixun homeworks whose
legacy `/myshixuns/{id}.json` lookup no longer returns `game_identifier`.

## Requirements

* Preserve existing course and homework selection behavior.
* Resolve `game_identifier` from Educoder's current shixun execution endpoint
  when the legacy myshixun lookup does not provide it.
* Keep downstream task detail, answer code, and submit flows using the existing
  `game_identifier` context.
* Do not print credentials, cookies, submitted code, or raw API payloads.

## Acceptance Criteria

* [x] `educoder task --course 112258 --homework 3635136 --json` returns task
      detail instead of the `无法获取 game_identifier` error.
* [x] Existing homework selection tests continue to pass.
* [x] Unit tests cover resolving `game_identifier` via the current
      `shixun_exec` fallback.
* [x] Lint, type check, and tests pass.

## Definition of Done

* Tests added or updated for the changed client behavior.
* `uv run ruff format --check .`, `uv run ruff check .`, `uv run ty check`, and
  `uv run pytest -q` pass.
* Spec update considered after implementation.

## Technical Approach

Add a small client-layer method for `GET
/shixuns/{shixun_identifier}/shixun_exec.json` with `homework_common_id`. Update
`select_homework()` or context resolution so it uses this method when needed and
stores the returned `game_identifier`.

## Decision (ADR-lite)

**Context**: The stored `myshixun_identifier` still appears in homework list
responses, but `/myshixuns/{id}.json` now returns 404. The current web client
uses `shixun_exec` and expects `game_identifier` in that response.

**Decision**: Use `shixun_exec` as the fallback source for task
`game_identifier`.

**Consequences**: The CLI matches the current web launch path while retaining
the existing API flow. If Educoder changes launch semantics again, the fallback
method is isolated in the client layer.

## Out of Scope

* Reworking credential storage or login behavior.
* Adding browser automation.
* Rewriting task submission or answer-code retrieval endpoints.
* Supporting Jupyter homework launch in this task.

## Research References

* [`research/api-resolution.md`](research/api-resolution.md) — current web task
  launch path returns `game_identifier` through `shixun_exec`.

## Technical Notes

* Likely files: `src/educoder_cli/client.py`, `tests/test_client.py`, possibly
  `tests/test_cli.py`.
* Existing error handling should remain `ValueError` at the client/context
  boundary and CLI conversion through `_handle_cli_error`.
