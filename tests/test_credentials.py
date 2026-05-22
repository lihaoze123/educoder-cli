import json
import stat

from educoder_cli.credentials import (
    StoredCredentials,
    default_credentials_path,
    load_credentials,
    save_credentials,
)


def test_default_credentials_path_uses_xdg_config_home(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

    assert default_credentials_path() == tmp_path / "educoder-cli" / "credentials.json"


def test_save_and_load_credentials_round_trip_with_restrictive_permissions(tmp_path) -> None:
    path = tmp_path / "config" / "credentials.json"
    credentials = StoredCredentials("zzud", "autologin", "session")

    saved_path = save_credentials(credentials, path)

    assert saved_path == path
    assert load_credentials(path) == credentials
    assert stat.S_IMODE(path.parent.stat().st_mode) == 0o700
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_load_credentials_returns_none_when_missing(tmp_path) -> None:
    assert load_credentials(tmp_path / "missing.json") is None


def test_load_credentials_rejects_incomplete_file(tmp_path) -> None:
    path = tmp_path / "credentials.json"
    path.write_text(json.dumps({"zzud": "zzud"}), encoding="utf-8")

    try:
        load_credentials(path)
    except ValueError as exc:
        assert "不完整" in str(exc)
    else:
        raise AssertionError("expected ValueError")
