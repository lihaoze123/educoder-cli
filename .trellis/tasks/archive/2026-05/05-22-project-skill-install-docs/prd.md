# Project Skill Install Docs

## Goal

Move the `educoder-cli` skill into this repository as distributable project content, add CLI installation prerequisites to the skill context, and document in README how users install the skill with `npx skills@latest add` so Agent tools can assist with EduCoder homework.

## What I Already Know

- User expects the skill to be named `educoder-cli` and live in the project directory, not only in `~/.codex/skills`.
- The earlier prototype lived under the user-level skills directory; the project source skill is named `educoder-cli`.
- The repo already has an empty `.codex/skills` directory, but `skills add <package>` scans a package/repository; a top-level `skills/educoder-cli` source directory is clearer for distribution.
- `npx skills@latest --help` confirms `add <package>` plus `--skill`, `--agent`, `--copy`, and `-y` options.
- README already documents installing `educoder-cli` via `uv tool install git+https://github.com/lihaoze123/educoder-cli`.

## Requirements

- Add the `educoder-cli` skill under this repository.
- Update the skill body/reference to include how to install `educoder-cli` before using the workflow.
- Keep the skill concise and valid per `$skill-creator`.
- Update README to explain:
  - install the CLI tool;
  - install the project skill with `npx skills@latest add`;
  - invoke the Agent with `$educoder-cli` to assist with homework.
- Verify the project skill validates with `quick_validate.py`.
- Verify `npx skills@latest add` can discover the project skill from the repo.
- Run project quality checks.

## Acceptance Criteria

- [x] `skills/educoder-cli/SKILL.md` exists.
- [x] `skills/educoder-cli/references/educoder-cli.md` exists and includes CLI install commands.
- [x] README includes `npx skills@latest add lihaoze123/educoder-cli --skill educoder-cli ...` installation guidance for the skill.
- [x] `quick_validate.py skills/educoder-cli` passes.
- [x] `npx skills@latest add ./skills/educoder-cli --list` or equivalent discovery succeeds.
- [x] Local quality checks pass.

## Out of Scope

- Changing application CLI behavior.
- Publishing to npm or a skill registry.
- Removing any existing user-level installed copy without explicit user request.

## Technical Notes

- Use top-level `skills/` as repository source content for distributable skills.
- Public install command uses `npx skills@latest add lihaoze123/educoder-cli --skill educoder-cli ...`.
- Keep `--skill educoder-cli` because repository-root discovery also sees Trellis internal skills under `.agents/skills`.
- Do not store credentials, downloaded source, or submitted code in docs.
- `npx skills@latest add ./skills/educoder-cli --list` found exactly one skill.
- `npx skills@latest add . --skill educoder-cli --agent codex --copy -y --list` found the project skill from the repository root and confirmed why README should keep `--skill educoder-cli`.
- Validation passed with `uv run python /home/chumeng/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/educoder-cli`.
- Project checks passed: `uv run ruff format --check .`, `uv run ruff check .`, `uv run ty check`, and `uv run pytest -q`.
