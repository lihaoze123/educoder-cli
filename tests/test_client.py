import httpx
import pytest

from educoder_cli.client import EduCoderClient
from educoder_cli.errors import SessionExpiredError, SignatureError


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
