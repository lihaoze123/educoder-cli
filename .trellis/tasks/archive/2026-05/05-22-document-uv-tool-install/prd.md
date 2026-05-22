# Document uv Tool Install Command

## Goal

Add a user-facing installation note showing that `educoder-cli` can be installed
directly from the GitHub repository with `uv tool install`.

## Requirements

- Update the README installation documentation.
- Include the exact command:
  `uv tool install git+https://github.com/lihaoze123/educoder-cli`
- Keep existing development environment setup instructions intact.

## Acceptance Criteria

- [x] README has a clear installation section before CLI usage examples.
- [x] The install command is spelled exactly as requested.
- [x] Development setup with `uv sync --all-extras --dev` remains available.

## Definition of Done

- Documentation updated.
- No code behavior changed.
- A lightweight verification confirms the README contains the command.

## Technical Approach

Add a short `## 安装` section near the top of `README.md`, before development
environment setup and CLI examples.

## Out of Scope

- Publishing package metadata changes.
- Changing CLI behavior or dependency configuration.

## Technical Notes

- Existing installation/development instructions were inspected in `README.md`.
- Backend spec index was reviewed; this task is documentation-only.
