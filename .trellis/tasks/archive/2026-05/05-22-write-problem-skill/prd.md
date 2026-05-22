# 撰写真实写题路径 Skill

## Goal

Create a reusable Codex skill that guides future agents through a real EduCoder writing/solving path using this repository's `educoder-cli`: authenticate, discover courses/homeworks, read the current task, fetch remote starter code, edit locally, submit when safe, and interpret results.

## What I Already Know

- User asked to run through a real 写题 path and write a skill using `$skill-creator`.
- This repository is `educoder-cli`, a Python CLI for 头歌 / EduCoder workflows.
- Existing commands cover the target path: `status`, `courses`, `homeworks`, `task`, `code`, and `submit`.
- `submit` saves code remotely and triggers evaluation, so it is a state-changing operation.
- `$skill-creator` defaults new skills to `${CODEX_HOME:-$HOME/.codex}/skills` when no destination is specified.

## Assumptions

- "写题" means using `educoder-cli` to solve/write code for an existing EduCoder homework task, not authoring new contest problems.
- The skill should be installed under `~/.codex/skills` so Codex can auto-discover it.
- A safe "real path" validation can run non-mutating CLI steps automatically; remote submit requires an explicit target or user confirmation.

## Requirements

- Create a skill named `educoder-solve-task`.
- Include concise trigger metadata that fires when the user asks Codex to solve/write an EduCoder/头歌 homework task.
- Encode the concrete CLI workflow:
  - verify credentials with `uv run educoder status`;
  - list courses and homeworks;
  - fetch task detail as text and JSON;
  - fetch remote answer/starter code to a local file;
  - inspect path, statement, tests, language/runtime cues, and prior compile output;
  - edit locally;
  - submit only when the user has selected a target and state-changing action is appropriate;
  - handle failed evaluation by reading feedback and iterating.
- Preserve credential and submitted-code safety: never print secrets, cookies, headers, or full remote payloads.
- Add a reference document for the exact CLI command path discovered from this repo.
- Validate the skill with the official `quick_validate.py` script.

## Acceptance Criteria

- [x] A real CLI path is exercised far enough to verify the installed command and authentication/discovery behavior, or a blocker is documented.
- [x] Skill folder exists at `${CODEX_HOME:-$HOME/.codex}/skills/educoder-solve-task`.
- [x] `SKILL.md` has valid frontmatter and actionable workflow instructions.
- [x] `agents/openai.yaml` exists and matches the skill.
- [x] Bundled references contain repo-specific command details.
- [x] `quick_validate.py` passes for the skill folder.
- [x] Repo quality checks are run for any in-repo changes.

## Out of Scope

- Adding new `educoder-cli` commands.
- Submitting to an arbitrary real homework without a user-selected target.
- Storing credentials, task payloads, or submitted source in Trellis artifacts.
- Creating extra README/CHANGELOG-style documentation inside the skill.

## Technical Notes

- README documents install/dev commands and the CLI solve path.
- `src/educoder_cli/cli.py` owns Typer commands and confirms `submit` accepts `--file`, waits by default, and exits non-zero on failed evaluation.
- `src/educoder_cli/client.py` confirms `submit` saves code first, triggers build/evaluation, and polls until pass/fail or timeout.
- `.trellis/spec/backend/index.md` requires keeping auth cookies, `zzud`, `_educoder_session`, request bodies, and submitted code out of logs/errors.
- Real path validation succeeded through `status`, `courses`, `homeworks`, `task`, and `code --output`; `submit` was intentionally skipped because it mutates remote homework state.
- Official skill validation passed with `uv run python /home/chumeng/.codex/skills/.system/skill-creator/scripts/quick_validate.py /home/chumeng/.codex/skills/educoder-solve-task`.
- Project checks passed: `uv run ruff format --check .`, `uv run ruff check .`, `uv run ty check`, and `uv run pytest -q`.
