# Database Guidelines

> Current persistence conventions for this project.

---

## Overview

This project currently has no database layer, ORM, migrations, or general local
cache. It is a CLI wrapper around remote Educoder API calls with one deliberate
filesystem persistence boundary: saved login state.

Persisted project data is source, tests, configuration, package metadata, and
the user credential file managed by `src/educoder_cli/credentials.py`. Runtime
workflow state still lives in memory on `EduCoderClient`:

- Credential-derived request state: `zzud`, `cookie`, `pc_auth`.
- Selected Educoder context: `course_identifier`, `homework_common_id`,
  `shixun_identifier`, `myshixun_identifier`, and `game_identifier`.

Reference: `src/educoder_cli/client.py` initializes those fields in
`EduCoderClient.__init__()` and mutates them through selection methods such as
`select_course()` and `select_homework()`.

## Credential Persistence Contract

Saved login state is intentionally narrow:

- Store only `zzud`, `autologin_trustie`, and `_educoder_session` equivalents.
- Do not store passwords, submitted code, request bodies, full headers, raw API
  payloads, or selected course/homework/game context.
- Use the user config directory, not the repository:
  - Linux/XDG: `$XDG_CONFIG_HOME/educoder-cli/credentials.json` when set.
  - Otherwise: `~/.config/educoder-cli/credentials.json` on Linux-like systems.
  - macOS and Windows may use their platform user config roots.
- Create the config directory with `0700` permissions and the credentials file
  with `0600` permissions where the platform supports POSIX modes.
- Authenticated commands resolve credentials in this priority order: explicit CLI
  options, environment variables, saved login state.
- A corrupt or incomplete saved credential file is a local error; ask the user to
  run `educoder login` again rather than silently ignoring it.

---

## Remote API Access Pattern

Treat Educoder as the persistence backend. New data access should be implemented
as methods on `EduCoderClient` using the existing request helpers:

```python
def _get(self, endpoint: str) -> JsonObject:
    return self._request("GET", endpoint)

def _post(self, endpoint: str, json_data: JsonObject) -> JsonObject:
    return self._request("POST", endpoint, json_data=json_data)
```

When an endpoint returns a stable shape, convert it to a dataclass model in
`models.py`, as `get_courses()` does with `Course.from_dict()`. When an endpoint
returns loose or workflow-specific data, keep using `JsonObject` until the shape
is stable enough to model.

---

## Migrations

There are no migrations. Do not introduce Alembic, SQLAlchemy, SQLite files,
general JSON caches, or ad hoc state directories for normal CLI behavior.

If a future feature needs additional local persistence beyond saved login state,
create a separate design task first. That design should specify:

- What user data is stored.
- Where it is stored.
- How passwords, credentials unrelated to the feature, submitted code, request
  bodies, and raw API payloads are kept out of local persistence.
- How tests isolate the storage backend.

---

## Naming Conventions

There are no table or column naming conventions because there are no local
tables. For remote API payloads:

- Preserve Educoder field names when building request bodies, such as
  `homework_common_id`, `challenge_id`, and `currentUserId`.
- Use Python snake_case for method parameters and dataclass attributes unless
  the name is deliberately mirroring an API key inside a request body.
- Keep endpoint path construction in `client.py`; do not duplicate query-string
  conventions in CLI commands.

---

## Common Mistakes

- Do not add persistence as a workaround for selected course/homework/game
  context. The current pattern is explicit selection followed by in-memory fields
  on `EduCoderClient`.
- Do not store passwords, request bodies, submitted code, or raw API payloads in
  logs or cache files.
- Do not print or log saved credential values while loading them.
- Do not introduce a database abstraction around `httpx`; remote API methods
  should stay on `EduCoderClient` until the package grows a real storage layer.
