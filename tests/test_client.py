import json

import httpx
import pytest

from educoder_cli.client import AmbiguousSelectionError, EduCoderClient
from educoder_cli.errors import EduCoderAPIError, SessionExpiredError, SignatureError
from educoder_cli.models import Challenge, Game, TaskDetail, User


def make_client(handler) -> EduCoderClient:
    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)
    return EduCoderClient("zzud", "autologin", "session", http_client=http_client)


def test_get_courses_parses_courses_and_sends_auth_headers() -> None:
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["authorization"] = request.headers["Pc-Authorization"]
        seen["cookie"] = request.headers["Cookie"]
        return httpx.Response(
            200,
            json={
                "courses": [
                    {
                        "id": 1,
                        "name": "Python",
                        "identifier": "py",
                        "school": "Computer School",
                        "tasks_count": 3,
                    }
                ]
            },
        )

    client = make_client(handler)

    courses = client.get_courses(page=2, limit=3)

    assert courses[0].id == 1
    assert courses[0].name == "Python"
    assert courses[0].tasks_count == 3
    assert "page=2" in seen["url"]
    assert "limit=3" in seen["url"]
    assert seen["authorization"] == "session"
    assert "autologin_trustie=autologin" in seen["cookie"]
    assert "_educoder_session=session" in seen["cookie"]


def test_request_raises_session_expired_on_401() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"message": "expired"})

    client = make_client(handler)

    with pytest.raises(SessionExpiredError) as exc_info:
        client.get_courses()

    assert exc_info.value.status_code == 401


def test_request_raises_signature_error_on_api_status() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"status": -102})

    client = make_client(handler)

    with pytest.raises(SignatureError):
        client.get_courses()


def test_login_posts_credentials_and_extracts_cookies() -> None:
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["authorization"] = request.headers["Pc-Authorization"]
        seen["has_cookie"] = "Cookie" in request.headers
        seen["origin"] = request.headers["Origin"]
        seen["referer"] = request.headers["Referer"]
        seen["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            headers=[
                ("set-cookie", "_educoder_session=session-token; Domain=.educoder.net; Path=/"),
                (
                    "set-cookie",
                    "autologin_trustie=auto-token; Domain=.educoder.net; Path=/",
                ),
            ],
            json={
                "user_id": 1,
                "login": "alice",
                "name": "Alice",
                "identity": "student",
                "school": "CS",
                "grade": 100,
            },
        )

    client = make_client(handler)

    result = client.login("phone-or-email", "secret")

    assert seen["url"].endswith("/accounts/login.json")
    assert seen["authorization"] == "null"
    assert seen["has_cookie"] is False
    assert seen["origin"] == "https://www.educoder.net"
    assert seen["referer"] == "https://www.educoder.net/login"
    assert seen["body"] == {
        "login": "phone-or-email",
        "password": "secret",
        "autologin": True,
        "tl": None,
        "source": None,
    }
    assert result.zzud == "alice"
    assert result.autologin == "auto-token"
    assert result.session == "session-token"
    assert client.pc_auth == "session-token"
    assert "_educoder_session=session-token" in client.cookie


def test_login_raises_api_error_on_invalid_credentials() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"status": -3, "message": "bad"})

    client = make_client(handler)

    with pytest.raises(EduCoderAPIError, match="用户名或密码错误"):
        client.login("alice", "wrong")


def test_select_course_raises_on_ambiguous_name_match() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "courses": [
                    {"id": 1, "name": "Python", "identifier": "py-1"},
                    {"id": 2, "name": "Python", "identifier": "py-2"},
                ]
            },
        )

    client = make_client(handler)

    with pytest.raises(AmbiguousSelectionError) as exc_info:
        client.select_course("Python")

    assert exc_info.value.target == "课堂"
    assert len(exc_info.value.candidates) == 2


def test_select_homework_raises_on_ambiguous_name_match() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "homeworks": [
                    {
                        "homework_id": 1,
                        "name": "实验",
                        "shixun_identifier": "s-1",
                        "myshixun_identifier": None,
                    },
                    {
                        "homework_id": 2,
                        "name": "实验",
                        "shixun_identifier": "s-2",
                        "myshixun_identifier": None,
                    },
                ]
            },
        )

    client = make_client(handler)
    client.course_identifier = "py"

    with pytest.raises(AmbiguousSelectionError) as exc_info:
        client.select_homework("实验")

    assert exc_info.value.target == "实验"
    assert len(exc_info.value.candidates) == 2


def test_submit_passes_timeout_to_poll_result(monkeypatch: pytest.MonkeyPatch) -> None:
    client = make_client(lambda _request: httpx.Response(200, json={}))
    client.myshixun_identifier = "my-1"
    task = TaskDetail(
        game=Game(id=10, identifier="game-1"),
        challenge=Challenge(id=20, path="main.py"),
        user=User(user_id=30),
        homework_common_id=40,
    )
    seen = {}

    monkeypatch.setattr(client, "get_current_context", lambda: task)
    monkeypatch.setattr(
        client,
        "save_code",
        lambda *_args, **_kwargs: {"content": {"commitID": "commit-1"}, "sec_key": "sec-1"},
    )
    monkeypatch.setattr(client, "game_build", lambda *_args, **_kwargs: {})

    def fake_poll(interval: float, timeout: int) -> dict[str, object]:
        seen["interval"] = interval
        seen["timeout"] = timeout
        return {"task_detail": task, "passed": True, "test_sets": []}

    monkeypatch.setattr(client, "_poll_result", fake_poll)

    result = client.submit("print(1)", poll_interval=0.5, timeout=99)

    assert result["passed"] is True
    assert seen == {"interval": 0.5, "timeout": 99}
