import json
from pathlib import Path
from typing import ClassVar, Self

import pytest
from typer.testing import CliRunner

from educoder_cli import cli
from educoder_cli.credentials import StoredCredentials
from educoder_cli.errors import EduCoderAPIError
from educoder_cli.models import (
    Challenge,
    Course,
    Game,
    HomeworkCommon,
    LoginResult,
    TaskDetail,
    User,
)
from educoder_cli.models import (
    TestSet as ModelTestSet,
)

runner = CliRunner()
AUTH_ENV = {
    "EDUCODER_ZZUD": "zzud",
    "EDUCODER_AUTOLOGIN": "autologin",
    "EDUCODER_SESSION": "session",
}


def make_task_detail(status: int = 2) -> TaskDetail:
    return TaskDetail(
        game=Game(id=10, identifier="game-1", status=status, final_score=100.0),
        challenge=Challenge(id=20, subject="关卡一", position=1, path="main.py；"),
        user=User(user_id=30, login="alice", name="Alice"),
        test_sets=[
            ModelTestSet(
                result=status == 2,
                output="ok",
                actual_output="ok",
                is_public=True,
                ts_time=0.1,
                ts_mem=1.0,
            )
        ],
        homework_common_id=42,
        homework_common_name="实验一",
        game_count=1,
        time_limit=10,
    )


class FakeClient:
    instances: ClassVar[list["FakeClient"]] = []
    course: ClassVar[Course] = Course(
        id=1, name="Python", identifier="py", school="CS", tasks_count=2
    )
    homework: ClassVar[HomeworkCommon] = HomeworkCommon(
        homework_id=42,
        name="实验一",
        shixun_identifier="shixun-1",
        myshixun_identifier="my-1",
        status=["进行中"],
        challenge_count=3,
        finished_challenge_count=1,
        end_time="2026-06-01",
    )
    task_detail: ClassVar[TaskDetail] = make_task_detail()
    answer_code: ClassVar[str] = "print('remote')\n"
    submit_result: ClassVar[dict[str, object]] = {
        "task_detail": make_task_detail(),
        "passed": True,
        "test_sets": make_task_detail().test_sets,
    }
    login_result: ClassVar[LoginResult] = LoginResult(
        user_id="30",
        login="alice",
        name="Alice",
        identity="student",
        school="CS",
        grade="100",
        zzud="alice",
        autologin="auto-token",
        session="session-token",
    )
    raise_api_error: ClassVar[bool] = False

    def __init__(self, zzud: str = "", autologin: str = "", session: str = "") -> None:
        self.auth = (zzud, autologin, session)
        self.login_account: str | None = None
        self.login_password: str | None = None
        self.courses_page: int | None = None
        self.courses_limit: int | None = None
        self.course_selector: str | int | None = None
        self.homework_selector: str | int | None = None
        self.answer_code_path: str | None = None
        self.submitted_source: str | None = None
        self.submitted_wait: bool | None = None
        self.submitted_timeout: int | None = None
        self.submitted_poll_interval: float | None = None
        FakeClient.instances.append(self)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        return None

    def login(self, login: str, password: str) -> LoginResult:
        self.login_account = login
        self.login_password = password
        if self.raise_api_error:
            raise EduCoderAPIError("boom")
        return self.login_result

    def get_courses(self, page: int = 1, limit: int = 20) -> list[Course]:
        self.courses_page = page
        self.courses_limit = limit
        if self.raise_api_error:
            raise EduCoderAPIError("boom")
        return [self.course]

    def select_course(self, name_or_id: str | int) -> Course:
        self.course_selector = name_or_id
        return self.course

    def get_homeworks(self) -> list[HomeworkCommon]:
        if self.raise_api_error:
            raise EduCoderAPIError("boom")
        return [self.homework]

    def select_homework(self, identifier: str | int) -> HomeworkCommon:
        self.homework_selector = identifier
        return self.homework

    def get_current_context(self) -> TaskDetail:
        return self.task_detail

    def get_answer_code(self, code_path: str | None = None) -> str:
        self.answer_code_path = code_path
        return self.answer_code

    def submit(
        self,
        code: str,
        *,
        wait: bool = True,
        poll_interval: float = 2.0,
        timeout: int = 30,
    ) -> dict[str, object]:
        self.submitted_source = code
        self.submitted_wait = wait
        self.submitted_poll_interval = poll_interval
        self.submitted_timeout = timeout
        return self.submit_result


@pytest.fixture(autouse=True)
def fake_client(monkeypatch: pytest.MonkeyPatch) -> None:
    FakeClient.instances = []
    FakeClient.task_detail = make_task_detail()
    FakeClient.answer_code = "print('remote')\n"
    FakeClient.submit_result = {
        "task_detail": make_task_detail(),
        "passed": True,
        "test_sets": make_task_detail().test_sets,
    }
    FakeClient.login_result = LoginResult(
        user_id="30",
        login="alice",
        name="Alice",
        identity="student",
        school="CS",
        grade="100",
        zzud="alice",
        autologin="auto-token",
        session="session-token",
    )
    FakeClient.raise_api_error = False
    monkeypatch.setattr(cli, "EduCoderClient", FakeClient)
    monkeypatch.setattr(cli, "load_credentials", lambda: None)
    monkeypatch.setattr(
        cli,
        "save_credentials",
        lambda _credentials: Path("/tmp/educoder-cli/credentials.json"),
    )


def test_login_json_persists_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    saved_credentials = []

    def fake_save(credentials: StoredCredentials) -> Path:
        saved_credentials.append(credentials)
        return Path("/tmp/educoder-cli/credentials.json")

    monkeypatch.setattr(cli, "save_credentials", fake_save)

    result = runner.invoke(
        cli.app,
        ["login", "--login", "alice", "--password", "secret", "--json"],
    )

    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["user"]["login"] == "alice"
    assert data["saved"] is True
    assert data["credentials_path"] == "/tmp/educoder-cli/credentials.json"
    client = FakeClient.instances[-1]
    assert client.auth == ("", "", "")
    assert client.login_account == "alice"
    assert client.login_password == "secret"
    assert saved_credentials == [StoredCredentials("alice", "auto-token", "session-token")]


def test_login_text_reports_saved_state_without_secrets() -> None:
    result = runner.invoke(
        cli.app,
        ["login", "--login", "alice", "--password", "secret"],
    )

    assert result.exit_code == 0
    assert "Logged in as Alice" in result.stdout
    assert "Saved login state" in result.stdout
    assert "session-token" not in result.stdout
    assert "auto-token" not in result.stdout
    assert "secret" not in result.stdout


def test_status_json_checks_credentials_with_course_probe() -> None:
    result = runner.invoke(cli.app, ["status", "--json"], env=AUTH_ENV)

    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data == {"authenticated": True, "probe": "courses", "courses_checked": 1}
    client = FakeClient.instances[-1]
    assert client.auth == ("zzud", "autologin", "session")
    assert client.courses_page == 1
    assert client.courses_limit == 1


def test_status_env_credentials_do_not_read_saved_state(monkeypatch: pytest.MonkeyPatch) -> None:
    def raise_if_loaded() -> StoredCredentials:
        raise ValueError("should not load")

    monkeypatch.setattr(cli, "load_credentials", raise_if_loaded)

    result = runner.invoke(cli.app, ["status", "--json"], env=AUTH_ENV)

    assert result.exit_code == 0
    client = FakeClient.instances[-1]
    assert client.auth == ("zzud", "autologin", "session")


def test_status_uses_stored_credentials_when_env_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        cli,
        "load_credentials",
        lambda: StoredCredentials("stored-zzud", "stored-auto", "stored-session"),
    )

    result = runner.invoke(cli.app, ["status", "--json"])

    assert result.exit_code == 0
    client = FakeClient.instances[-1]
    assert client.auth == ("stored-zzud", "stored-auto", "stored-session")


def test_homeworks_uses_stored_credentials_when_env_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        cli,
        "load_credentials",
        lambda: StoredCredentials("stored-zzud", "stored-auto", "stored-session"),
    )

    result = runner.invoke(cli.app, ["homeworks", "--course", "py", "--json"])

    assert result.exit_code == 0
    client = FakeClient.instances[-1]
    assert client.auth == ("stored-zzud", "stored-auto", "stored-session")


def test_status_missing_credentials_exit_two() -> None:
    result = runner.invoke(
        cli.app,
        ["status"],
        env={"EDUCODER_ZZUD": "", "EDUCODER_AUTOLOGIN": "", "EDUCODER_SESSION": ""},
    )

    assert result.exit_code == 2
    assert "Missing required credentials" in result.stderr


def test_status_api_error_exits_one() -> None:
    FakeClient.raise_api_error = True

    result = runner.invoke(cli.app, ["status"], env=AUTH_ENV)

    assert result.exit_code == 1
    assert "boom" in result.stderr


def test_homeworks_json_outputs_selected_course_and_homeworks() -> None:
    result = runner.invoke(cli.app, ["homeworks", "--course", "py", "--json"], env=AUTH_ENV)

    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["course"]["identifier"] == "py"
    assert data["homeworks"][0]["homework_id"] == 42


def test_task_json_outputs_current_task_summary() -> None:
    result = runner.invoke(
        cli.app,
        ["task", "--course", "py", "--homework", "42", "--json"],
        env=AUTH_ENV,
    )

    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["task"]["challenge"]["path"] == "main.py"
    assert data["task"]["game"]["status_text"] == "通过"


def test_task_text_renders_nullable_test_set_fields() -> None:
    FakeClient.task_detail = make_task_detail(status=0)
    FakeClient.task_detail.test_sets = [
        ModelTestSet(
            result=None,
            output="expected",
            actual_output=None,
            is_public=True,
            ts_time=None,
            ts_mem=None,
        )
    ]

    result = runner.invoke(
        cli.app,
        ["task", "--course", "py", "--homework", "42"],
        env=AUTH_ENV,
    )

    assert result.exit_code == 0
    assert "Test Sets" in result.stdout
    assert "expected" in result.stdout


def test_code_outputs_remote_content_to_stdout() -> None:
    result = runner.invoke(
        cli.app,
        ["code", "--course", "py", "--homework", "42"],
        env=AUTH_ENV,
    )

    assert result.exit_code == 0
    assert result.stdout == "print('remote')\n"
    assert FakeClient.instances[-1].answer_code_path == "main.py"


def test_code_output_refuses_existing_file_without_force(tmp_path: Path) -> None:
    output = tmp_path / "main.py"
    output.write_text("local", encoding="utf-8")

    result = runner.invoke(
        cli.app,
        ["code", "--course", "py", "--homework", "42", "--output", str(output)],
        env=AUTH_ENV,
    )

    assert result.exit_code == 1
    assert output.read_text(encoding="utf-8") == "local"


def test_code_output_force_writes_file(tmp_path: Path) -> None:
    output = tmp_path / "main.py"
    output.write_text("local", encoding="utf-8")

    result = runner.invoke(
        cli.app,
        ["code", "--course", "py", "--homework", "42", "--output", str(output), "--force"],
        env=AUTH_ENV,
    )

    assert result.exit_code == 0
    assert output.read_text(encoding="utf-8") == "print('remote')\n"


def test_submit_reads_file_and_failing_evaluation_exits_one(tmp_path: Path) -> None:
    source = tmp_path / "main.py"
    source.write_text("print('local')\n", encoding="utf-8")
    FakeClient.submit_result = {
        "task_detail": make_task_detail(status=3),
        "passed": False,
        "test_sets": make_task_detail(status=3).test_sets,
    }

    result = runner.invoke(
        cli.app,
        ["submit", "--course", "py", "--homework", "42", "--file", str(source)],
        env=AUTH_ENV,
    )

    assert result.exit_code == 1
    assert FakeClient.instances[-1].submitted_source == "print('local')\n"
    assert "Evaluation failed" in result.stdout


def test_submit_reads_stdin_with_no_wait() -> None:
    FakeClient.submit_result = {
        "task_detail": make_task_detail(status=1),
        "passed": None,
        "test_sets": [],
    }

    result = runner.invoke(
        cli.app,
        [
            "submit",
            "--course",
            "py",
            "--homework",
            "42",
            "--file",
            "-",
            "--no-wait",
            "--timeout",
            "77",
            "--poll-interval",
            "0.5",
        ],
        input="print('stdin')\n",
        env=AUTH_ENV,
    )

    assert result.exit_code == 0
    client = FakeClient.instances[-1]
    assert client.submitted_source == "print('stdin')\n"
    assert client.submitted_wait is False
    assert client.submitted_timeout == 77
    assert client.submitted_poll_interval == 0.5


def test_missing_credentials_exit_two() -> None:
    result = runner.invoke(
        cli.app,
        ["homeworks", "--course", "py"],
        env={"EDUCODER_ZZUD": "", "EDUCODER_AUTOLOGIN": "", "EDUCODER_SESSION": ""},
    )

    assert result.exit_code == 2
    assert "Missing required credentials" in result.stderr


def test_api_error_exits_one() -> None:
    FakeClient.raise_api_error = True

    result = runner.invoke(cli.app, ["homeworks", "--course", "py"], env=AUTH_ENV)

    assert result.exit_code == 1
    assert "boom" in result.stderr
