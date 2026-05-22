# Educoder Task Identifier Resolution

## Finding

The existing CLI resolves a homework by reading `myshixun_identifier` from the
course homework list, then calling:

```text
GET /api/myshixuns/{myshixun_identifier}.json
```

That endpoint currently returns `status: 404` for known homework
`myshixun_identifier` values, including completed homework contexts.

The current Educoder web bundle resolves classroom shixun homework entry through:

```text
GET /api/shixuns/{shixun_identifier}/shixun_exec.json
```

with `homework_common_id` in the query params. The response contains
`game_identifier` directly. For homework `3635136` (`shixun_identifier:
jnt7aplo`, `homework_common_id: 3635136`) this endpoint returned a valid
`game_identifier`.

## Implementation Implication

Keep existing homework selection behavior, but when `game_identifier` is absent,
fall back to `shixun_exec` using the already parsed `shixun_identifier` and
`homework_common_id`. This matches the web client's current task-launch path and
does not require changing downstream task detail, code retrieval, or submission
endpoints.
