import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Self

from educoder_cli.models import LoginResult

APP_DIR_NAME = "educoder-cli"
CREDENTIALS_FILE_NAME = "credentials.json"


@dataclass(frozen=True)
class StoredCredentials:
    zzud: str
    autologin: str
    session: str

    @classmethod
    def from_login_result(cls, result: LoginResult) -> Self:
        return cls(
            zzud=result.zzud,
            autologin=result.autologin,
            session=result.session,
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        credentials = cls(
            zzud=str(data.get("zzud") or ""),
            autologin=str(data.get("autologin") or ""),
            session=str(data.get("session") or ""),
        )
        if not credentials.zzud or not credentials.autologin or not credentials.session:
            raise ValueError("保存的登录状态不完整，请重新运行 educoder login")
        return credentials

    def to_dict(self) -> dict[str, str]:
        return {
            "zzud": self.zzud,
            "autologin": self.autologin,
            "session": self.session,
        }

    def as_tuple(self) -> tuple[str, str, str]:
        return self.zzud, self.autologin, self.session


def default_credentials_path() -> Path:
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config_home:
        return Path(xdg_config_home) / APP_DIR_NAME / CREDENTIALS_FILE_NAME

    if sys.platform == "darwin":
        return (
            Path.home() / "Library" / "Application Support" / APP_DIR_NAME / CREDENTIALS_FILE_NAME
        )

    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / APP_DIR_NAME / CREDENTIALS_FILE_NAME

    return Path.home() / ".config" / APP_DIR_NAME / CREDENTIALS_FILE_NAME


def load_credentials(path: Path | None = None) -> StoredCredentials | None:
    credentials_path = path or default_credentials_path()
    if not credentials_path.exists():
        return None

    try:
        raw_data = json.loads(credentials_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("无法读取保存的登录状态，请重新运行 educoder login") from exc

    if not isinstance(raw_data, dict):
        raise ValueError("保存的登录状态格式无效，请重新运行 educoder login")

    return StoredCredentials.from_dict(raw_data)


def save_credentials(credentials: StoredCredentials, path: Path | None = None) -> Path:
    credentials_path = path or default_credentials_path()
    data = json.dumps(credentials.to_dict(), ensure_ascii=False, indent=2) + "\n"
    temp_path = credentials_path.with_name(f".{credentials_path.name}.tmp")

    try:
        credentials_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(credentials_path.parent, 0o700)
        temp_path.write_text(data, encoding="utf-8")
        os.chmod(temp_path, 0o600)
        temp_path.replace(credentials_path)
        os.chmod(credentials_path, 0o600)
    except OSError as exc:
        raise ValueError("无法保存登录状态") from exc

    return credentials_path
