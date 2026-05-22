# EduCoder Login API Research

Source: `temp-阅后删除-educoder_login_research.md`

## Findings

- Login uses `POST https://data.educoder.net/api/accounts/login.json`.
- Headers follow the existing Educoder signing protocol: `X-EDU-Type: pc`,
  per-request `X-EDU-Timestamp`, per-request `X-EDU-Signature`, `Accept:
  application/json`, `Content-Type: application/json; charset=utf-8`, plus
  login-specific `Origin: https://www.educoder.net`, `Referer:
  https://www.educoder.net/login`, and pre-login `Pc-Authorization: null`.
- Request JSON body:

```json
{
  "login": "<username_or_phone_or_email>",
  "password": "<password>",
  "autologin": true,
  "tl": null,
  "source": null
}
```

- Successful login returns user profile fields and sets `_educoder_session` and
  `autologin_trustie` cookies.
- Follow-up API calls use `_educoder_session` as `Pc-Authorization` and include
  both cookies in the `Cookie` header.
- The research document's follow-up example uses `zzud=<login>` in the courses
  URL. The login response does not document a separate `zzud` cookie/value.
- Known API error statuses: `-3` invalid username/password, `-4` account needs a
  phone or email binding, `-5` other business error with message, `-102`
  signature failure.

## Repo Mapping

- `src/educoder_cli/signature.py` already implements the documented signing
  algorithm.
- `src/educoder_cli/client.py` already centralizes signed request behavior in
  `EduCoderClient._request()`, but its constructor currently requires existing
  `zzud`, `autologin_trustie`, and `_educoder_session` values.
- `src/educoder_cli/cli.py` currently treats credentials as stateless input via
  env vars/options and does not persist runtime state.

## Proposed MVP

- Add a client login method that reuses existing request normalization and parses
  `httpx` response cookies.
- Return a structured login result containing profile fields plus `zzud`,
  `autologin_trustie`, and `_educoder_session` values for the user to export.
- Use the login identifier as `zzud` unless a response field or cookie provides a
  better value.
- Add a health/status command that verifies supplied credentials by making a
  lightweight authenticated call, likely the current `get_courses(page=1,
  limit=1)` path.
