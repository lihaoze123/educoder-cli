from educoder_cli.models import Course, HomeworkCommon, LoginResult, TaskDetail
from educoder_cli.models import TestSet as ModelTestSet


def test_login_result_from_dict_uses_response_login_as_zzud() -> None:
    result = LoginResult.from_dict(
        {
            "user_id": 1,
            "login": "alice",
            "name": "Alice",
            "identity": "student",
            "school": "CS",
            "grade": 100,
        },
        fallback_zzud="phone-or-email",
        autologin="auto-token",
        session="session-token",
    )

    assert result.user_id == "1"
    assert result.zzud == "alice"
    assert result.autologin == "auto-token"
    assert result.session == "session-token"


def test_course_from_dict_uses_defaults() -> None:
    course = Course.from_dict({"id": 1, "name": "Python", "identifier": "py"})

    assert course.id == 1
    assert course.name == "Python"
    assert course.identifier == "py"
    assert course.school == ""
    assert course.is_accessible is True


def test_homework_from_dict_parses_optional_identifier() -> None:
    homework = HomeworkCommon.from_dict(
        {
            "homework_id": 42,
            "name": "实验一",
            "shixun_identifier": "shixun-1",
            "myshixun_identifier": None,
            "status": ["进行中"],
        }
    )

    assert homework.homework_id == 42
    assert homework.myshixun_identifier is None
    assert homework.status == ["进行中"]
    assert homework.challenge_count == 0


def test_task_detail_from_dict_parses_nested_models() -> None:
    detail = TaskDetail.from_dict(
        {
            "game": {"id": 10, "identifier": "game-1", "status": 2},
            "challenge": {"id": 20, "path": "main.py；"},
            "user": {"user_id": 30, "login": "alice"},
            "test_sets": [{"result": True, "output": "ok"}],
            "shixun_environments": [{"shixun_environment_id": 40, "name": "Python"}],
            "homework_common_id": 50,
            "next_game": "game-2",
        }
    )

    assert detail.game.id == 10
    assert detail.game.status == 2
    assert detail.challenge.clean_path == "main.py"
    assert detail.user.login == "alice"
    assert detail.test_sets[0].result is True
    assert detail.shixun_environments[0].shixun_environment_id == 40
    assert detail.homework_common_id == 50
    assert detail.next_game == "game-2"


def test_test_set_from_dict_preserves_nullable_execution_fields() -> None:
    test_set = ModelTestSet.from_dict(
        {
            "result": None,
            "output": "expected",
            "actual_output": None,
            "compile_success": None,
            "is_public": True,
            "ts_time": None,
            "ts_mem": None,
        }
    )

    assert test_set.result is None
    assert test_set.output == "expected"
    assert test_set.actual_output is None
    assert test_set.compile_success is None
    assert test_set.is_public is True
    assert test_set.ts_time is None
    assert test_set.ts_mem is None
