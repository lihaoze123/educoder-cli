# skills CLI Add Usage

## Command Checked

```bash
npx skills@latest --help
```

## Findings

- `skills add <package>` installs a skill package.
- Examples show GitHub shorthand and GitHub URL packages, but local package paths are accepted by the command shape.
- Relevant add options:
  - `--agent <agents>` installs to selected Agent tools.
  - `--skill <skills>` installs selected skills by name.
  - `--copy` copies files instead of symlinking into agent directories.
  - `-y` skips confirmation prompts.
  - `--full-depth` searches all subdirectories even when a root `SKILL.md` exists.
  - `--list` lists available skills without installing.

## Planned README Command

For users installing from GitHub:

```bash
npx skills@latest add lihaoze123/educoder-cli --skill educoder-cli --agent codex --copy -y
```

Use `--agent '*'` or omit `--agent` if the user wants another supported Agent tool.

## Discovery Checks

- `npx skills@latest add . --skill educoder-cli --agent codex --copy -y --list` found the project skill from the repository root, but also discovered Trellis internal skills under `.agents/skills`.
- `npx skills@latest add ./skills/educoder-cli --list` found exactly one skill and remains the local development discovery check.
- README uses the GitHub shorthand package `lihaoze123/educoder-cli` plus `--skill educoder-cli`; the remote command is expected to work after the skill files are committed and pushed.
