import sys
from pathlib import Path
from typing import Annotated, Any, NoReturn

import typer
from rich.console import Console
from rich.markup import escape
from rich.table import Table

from educoder_cli import __version__
from educoder_cli.client import AmbiguousSelectionError, EduCoderClient
from educoder_cli.errors import EduCoderAPIError
from educoder_cli.models import Course, HomeworkCommon, TaskDetail, TestSet

app = typer.Typer(no_args_is_help=True, help="Educoder / 头歌 command line client.")
console = Console()
err_console = Console(stderr=True)

ZzudOption = Annotated[
    str | None,
    typer.Option("--zzud", envvar="EDUCODER_ZZUD", help="Educoder zzud value."),
]
AutologinOption = Annotated[
    str | None,
    typer.Option(
        "--autologin",
        envvar="EDUCODER_AUTOLOGIN",
        help="autologin_trustie cookie value.",
    ),
]
SessionOption = Annotated[
    str | None,
    typer.Option(
        "--session",
        envvar="EDUCODER_SESSION",
        help="_educoder_session cookie value.",
    ),
]
JsonOption = Annotated[bool, typer.Option("--json", help="Output JSON.")]
CourseOption = Annotated[
    str,
    typer.Option("--course", help="Course ID, identifier, or name fragment."),
]
HomeworkOption = Annotated[
    str,
    typer.Option("--homework", help="Homework ID or name fragment."),
]


def _require_credentials(
    zzud: str | None,
    autologin: str | None,
    session: str | None,
) -> tuple[str, str, str]:
    missing = []
    if not zzud:
        missing.append("EDUCODER_ZZUD")
    if not autologin:
        missing.append("EDUCODER_AUTOLOGIN")
    if not session:
        missing.append("EDUCODER_SESSION")

    if missing:
        err_console.print("[red]Missing required credentials:[/red] " + ", ".join(missing))
        raise typer.Exit(2)

    assert zzud is not None
    assert autologin is not None
    assert session is not None
    return zzud, autologin, session


def _print_json(data: Any) -> None:
    console.print_json(data=data, ensure_ascii=False, highlight=False)


def _print_error(exc: Exception) -> None:
    err_console.print(f"[red]{escape(str(exc))}[/red]")
    if isinstance(exc, AmbiguousSelectionError):
        _print_ambiguous_candidates(exc)


def _print_ambiguous_candidates(exc: AmbiguousSelectionError) -> None:
    if all(isinstance(candidate, Course) for candidate in exc.candidates):
        table = Table(title=f"候选{exc.target}")
        table.add_column("ID", justify="right")
        table.add_column("Name")
        table.add_column("Identifier")
        table.add_column("School")
        for candidate in exc.candidates:
            if isinstance(candidate, Course):
                table.add_row(
                    str(candidate.id),
                    escape(candidate.name),
                    escape(candidate.identifier),
                    escape(candidate.school),
                )
        err_console.print(table)
        return

    table = Table(title=f"候选{exc.target}")
    table.add_column("ID", justify="right")
    table.add_column("Name")
    table.add_column("Progress")
    table.add_column("Status")
    table.add_column("End Time")
    for candidate in exc.candidates:
        if isinstance(candidate, HomeworkCommon):
            table.add_row(
                str(candidate.homework_id),
                escape(candidate.name),
                _format_progress(candidate),
                escape(_format_status(candidate.status)),
                escape(candidate.end_time),
            )
    err_console.print(table)


def _handle_cli_error(exc: EduCoderAPIError | ValueError) -> NoReturn:
    _print_error(exc)
    raise typer.Exit(1) from exc


def _select_course_and_homework(
    client: EduCoderClient,
    course: str,
    homework: str,
) -> tuple[Course, HomeworkCommon]:
    selected_course = client.select_course(course)
    selected_homework = client.select_homework(homework)
    return selected_course, selected_homework


def _format_status(status: list[str]) -> str:
    return "、".join(status) if status else ""


def _format_progress(homework: HomeworkCommon) -> str:
    return f"{homework.finished_challenge_count}/{homework.challenge_count}"


def _truncate(value: str, limit: int = 600) -> str:
    if len(value) <= limit:
        return value
    return value[: limit - 1] + "…"


def _game_status(value: int) -> str:
    labels = {
        0: "未开始",
        1: "评测中",
        2: "通过",
        3: "未通过",
    }
    return labels.get(value, str(value))


def _course_to_dict(course: Course) -> dict[str, object]:
    return {
        "id": course.id,
        "name": course.name,
        "identifier": course.identifier,
        "school": course.school,
        "creator": course.creator,
        "tasks_count": course.tasks_count,
        "course_members_count": course.course_members_count,
        "is_end": course.is_end,
        "is_accessible": course.is_accessible,
    }


def _homework_to_dict(homework: HomeworkCommon) -> dict[str, object]:
    return {
        "homework_id": homework.homework_id,
        "name": homework.name,
        "shixun_identifier": homework.shixun_identifier,
        "myshixun_identifier": homework.myshixun_identifier,
        "status": homework.status,
        "time_status": homework.time_status,
        "challenge_count": homework.challenge_count,
        "finished_challenge_count": homework.finished_challenge_count,
        "checked_challenge_count": homework.checked_challenge_count,
        "shixun_finished_status": homework.shixun_finished_status,
        "publish_time": homework.publish_time,
        "end_time": homework.end_time,
        "upper_category_name": homework.upper_category_name,
        "author": homework.author,
    }


def _test_set_to_dict(test_set: TestSet) -> dict[str, object]:
    return {
        "result": test_set.result,
        "output": test_set.output,
        "actual_output": test_set.actual_output,
        "compile_success": test_set.compile_success,
        "is_public": test_set.is_public,
        "ts_time": test_set.ts_time,
        "ts_mem": test_set.ts_mem,
    }


def _task_detail_to_dict(task: TaskDetail) -> dict[str, object]:
    return {
        "homework_common_id": task.homework_common_id,
        "homework_common_name": task.homework_common_name,
        "game_count": task.game_count,
        "time_limit": task.time_limit,
        "prev_game": task.prev_game,
        "next_game": task.next_game,
        "last_compile_output": task.last_compile_output,
        "game": {
            "id": task.game.id,
            "identifier": task.game.identifier,
            "status": task.game.status,
            "status_text": _game_status(task.game.status),
            "final_score": task.game.final_score,
            "challenge_id": task.game.challenge_id,
            "accuracy": task.game.accuracy,
            "cost_time": task.game.cost_time,
        },
        "challenge": {
            "id": task.challenge.id,
            "subject": task.challenge.subject,
            "position": task.challenge.position,
            "score": task.challenge.score,
            "path": task.challenge.clean_path,
            "difficulty": task.challenge.difficulty,
            "task_pass": task.challenge.task_pass,
            "exec_time": task.challenge.exec_time,
        },
        "user": {
            "user_id": task.user.user_id,
            "login": task.user.login,
            "name": task.user.name,
            "identity": task.user.identity,
        },
        "test_sets": [_test_set_to_dict(test_set) for test_set in task.test_sets],
        "shixun_environments": [
            {
                "shixun_environment_id": environment.shixun_environment_id,
                "name": environment.name,
                "tab_type": environment.tab_type,
                "resource_type": environment.resource_type,
            }
            for environment in task.shixun_environments
        ],
    }


def _submission_to_dict(result: dict[str, Any]) -> dict[str, object]:
    task = result.get("task_detail")
    test_sets = result.get("test_sets", [])
    return {
        "passed": result.get("passed"),
        "task": _task_detail_to_dict(task) if isinstance(task, TaskDetail) else None,
        "test_sets": [
            _test_set_to_dict(test_set) for test_set in test_sets if isinstance(test_set, TestSet)
        ],
    }


def _render_homeworks(homeworks_: list[HomeworkCommon]) -> None:
    table = Table(title="Homeworks")
    table.add_column("ID", justify="right")
    table.add_column("Name")
    table.add_column("Progress")
    table.add_column("Status")
    table.add_column("End Time")

    for homework in homeworks_:
        table.add_row(
            str(homework.homework_id),
            escape(homework.name),
            _format_progress(homework),
            escape(_format_status(homework.status)),
            escape(homework.end_time),
        )

    console.print(table)


def _render_task_detail(task: TaskDetail, *, title: str = "Task") -> None:
    table = Table(title=title)
    table.add_column("Field")
    table.add_column("Value")
    table.add_row("Homework", escape(task.homework_common_name))
    table.add_row("Challenge", escape(task.challenge.subject))
    table.add_row("Position", str(task.challenge.position))
    table.add_row("Path", escape(task.challenge.clean_path))
    table.add_row("Game", escape(task.game.identifier))
    table.add_row("Status", _game_status(task.game.status))
    table.add_row("Score", str(task.game.final_score))
    table.add_row("Time Limit", str(task.time_limit))
    table.add_row("Prev Game", escape(task.prev_game or ""))
    table.add_row("Next Game", escape(task.next_game or ""))
    if task.last_compile_output:
        table.add_row("Last Compile Output", escape(_truncate(task.last_compile_output)))
    console.print(table)
    _render_test_sets(task.test_sets)


def _render_test_sets(test_sets: list[TestSet]) -> None:
    if not test_sets:
        return

    table = Table(title="Test Sets")
    table.add_column("#", justify="right")
    table.add_column("Result")
    table.add_column("Public")
    table.add_column("Time", justify="right")
    table.add_column("Memory", justify="right")
    table.add_column("Expected")
    table.add_column("Actual")
    for index, test_set in enumerate(test_sets, start=1):
        table.add_row(
            str(index),
            "pass" if test_set.result else "fail",
            "yes" if test_set.is_public else "no",
            str(test_set.ts_time),
            str(test_set.ts_mem),
            escape(_truncate(test_set.output, 120)),
            escape(_truncate(test_set.actual_output, 120)),
        )
    console.print(table)


def _render_submission(result: dict[str, Any]) -> None:
    passed = result.get("passed")
    if passed is None:
        console.print("[green]Submission triggered; evaluation was not waited.[/green]")
    elif passed:
        console.print("[green]Evaluation passed.[/green]")
    else:
        console.print("[red]Evaluation failed.[/red]")

    task = result.get("task_detail")
    if isinstance(task, TaskDetail):
        _render_task_detail(task, title="Submission")
        return

    test_sets = result.get("test_sets", [])
    _render_test_sets([test_set for test_set in test_sets if isinstance(test_set, TestSet)])


def _read_code_file(file: str) -> str:
    if file == "-":
        return sys.stdin.read()

    path = Path(file)
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"无法读取代码文件: {path}") from exc


def _write_output_file(path: Path, content: str, *, force: bool) -> None:
    if path.exists() and not force:
        raise ValueError(f"输出文件已存在: {path}，使用 --force 覆盖")
    try:
        path.write_text(content, encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"无法写入输出文件: {path}") from exc


@app.command()
def version() -> None:
    """Show the installed educoder-cli version."""
    console.print(f"educoder-cli {__version__}")


@app.command()
def courses(
    zzud: ZzudOption = None,
    autologin: AutologinOption = None,
    session: SessionOption = None,
    page: Annotated[int, typer.Option("--page", min=1, help="Course list page.")] = 1,
    limit: Annotated[int, typer.Option("--limit", min=1, help="Courses per page.")] = 20,
    json_output: JsonOption = False,
) -> None:
    """List courses for the authenticated account."""
    auth = _require_credentials(zzud, autologin, session)

    try:
        with EduCoderClient(*auth) as client:
            courses_ = client.get_courses(page=page, limit=limit)
    except EduCoderAPIError as exc:
        _handle_cli_error(exc)

    if json_output:
        _print_json([_course_to_dict(course) for course in courses_])
        return

    table = Table(title="Courses")
    table.add_column("ID", justify="right")
    table.add_column("Name")
    table.add_column("Identifier")
    table.add_column("School")
    table.add_column("Tasks", justify="right")

    for course in courses_:
        table.add_row(
            str(course.id),
            escape(course.name),
            escape(course.identifier),
            escape(course.school),
            str(course.tasks_count),
        )

    console.print(table)


@app.command()
def homeworks(
    course: CourseOption,
    zzud: ZzudOption = None,
    autologin: AutologinOption = None,
    session: SessionOption = None,
    json_output: JsonOption = False,
) -> None:
    """List shixun homeworks for a course."""
    auth = _require_credentials(zzud, autologin, session)

    try:
        with EduCoderClient(*auth) as client:
            selected_course = client.select_course(course)
            homeworks_ = client.get_homeworks()
    except (EduCoderAPIError, ValueError) as exc:
        _handle_cli_error(exc)

    if json_output:
        _print_json(
            {
                "course": _course_to_dict(selected_course),
                "homeworks": [_homework_to_dict(homework) for homework in homeworks_],
            }
        )
        return

    _render_homeworks(homeworks_)


@app.command(name="task")
def task_command(
    course: CourseOption,
    homework: HomeworkOption,
    zzud: ZzudOption = None,
    autologin: AutologinOption = None,
    session: SessionOption = None,
    json_output: JsonOption = False,
) -> None:
    """Show the current task detail for a homework."""
    auth = _require_credentials(zzud, autologin, session)

    try:
        with EduCoderClient(*auth) as client:
            selected_course, selected_homework = _select_course_and_homework(
                client, course, homework
            )
            detail = client.get_current_context()
    except (EduCoderAPIError, ValueError) as exc:
        _handle_cli_error(exc)

    if json_output:
        _print_json(
            {
                "course": _course_to_dict(selected_course),
                "homework": _homework_to_dict(selected_homework),
                "task": _task_detail_to_dict(detail),
            }
        )
        return

    _render_task_detail(detail)


@app.command()
def code(
    course: CourseOption,
    homework: HomeworkOption,
    zzud: ZzudOption = None,
    autologin: AutologinOption = None,
    session: SessionOption = None,
    code_path: Annotated[
        str | None,
        typer.Option("--path", help="Remote code path override."),
    ] = None,
    output: Annotated[
        Path | None,
        typer.Option("--output", "-o", help="Write remote code to a local file."),
    ] = None,
    force: Annotated[bool, typer.Option("--force", help="Overwrite output file.")] = False,
    json_output: JsonOption = False,
) -> None:
    """Read current remote answer code."""
    auth = _require_credentials(zzud, autologin, session)

    try:
        with EduCoderClient(*auth) as client:
            selected_course, selected_homework = _select_course_and_homework(
                client, course, homework
            )
            detail = client.get_current_context()
            remote_path = code_path or detail.challenge.clean_path
            content = client.get_answer_code(code_path=remote_path)
        if output is not None:
            _write_output_file(output, content, force=force)
    except (EduCoderAPIError, ValueError) as exc:
        _handle_cli_error(exc)

    if json_output:
        data: dict[str, object] = {
            "course": _course_to_dict(selected_course),
            "homework": _homework_to_dict(selected_homework),
            "path": remote_path,
        }
        if output is None:
            data["content"] = content
        else:
            data["output"] = str(output)
            data["written"] = True
        _print_json(data)
        return

    if output is None:
        sys.stdout.write(content)
        return

    console.print(f"Wrote {escape(str(output))}")


@app.command()
def submit(
    course: CourseOption,
    homework: HomeworkOption,
    file: Annotated[
        str,
        typer.Option("--file", "-f", help="Local code file path, or '-' for stdin."),
    ],
    zzud: ZzudOption = None,
    autologin: AutologinOption = None,
    session: SessionOption = None,
    no_wait: Annotated[
        bool,
        typer.Option("--no-wait", help="Submit without waiting for evaluation."),
    ] = False,
    timeout: Annotated[
        int,
        typer.Option("--timeout", min=1, help="Evaluation polling timeout in seconds."),
    ] = 30,
    poll_interval: Annotated[
        float,
        typer.Option("--poll-interval", min=0.1, help="Polling interval in seconds."),
    ] = 2.0,
    json_output: JsonOption = False,
) -> None:
    """Submit local code to the current homework task."""
    auth = _require_credentials(zzud, autologin, session)

    try:
        source = _read_code_file(file)
        with EduCoderClient(*auth) as client:
            selected_course, selected_homework = _select_course_and_homework(
                client, course, homework
            )
            result = client.submit(
                source,
                wait=not no_wait,
                poll_interval=poll_interval,
                timeout=timeout,
            )
    except (EduCoderAPIError, ValueError) as exc:
        _handle_cli_error(exc)

    if json_output:
        data = _submission_to_dict(result)
        data["course"] = _course_to_dict(selected_course)
        data["homework"] = _homework_to_dict(selected_homework)
        _print_json(data)
    else:
        _render_submission(result)

    if result.get("passed") is False:
        raise typer.Exit(1)
