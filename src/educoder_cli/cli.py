from typing import Annotated

import typer
from rich.console import Console
from rich.markup import escape
from rich.table import Table

from educoder_cli import __version__
from educoder_cli.client import EduCoderClient
from educoder_cli.errors import EduCoderAPIError

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


def _print_error(exc: Exception) -> None:
    err_console.print(f"[red]{escape(str(exc))}[/red]")


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
) -> None:
    """List courses for the authenticated account."""
    auth = _require_credentials(zzud, autologin, session)

    try:
        with EduCoderClient(*auth) as client:
            courses_ = client.get_courses(page=page, limit=limit)
    except EduCoderAPIError as exc:
        _print_error(exc)
        raise typer.Exit(1) from exc

    table = Table(title="Courses")
    table.add_column("ID", justify="right")
    table.add_column("Name")
    table.add_column("Identifier")
    table.add_column("School")
    table.add_column("Tasks", justify="right")

    for course in courses_:
        table.add_row(
            str(course.id),
            course.name,
            course.identifier,
            course.school,
            str(course.tasks_count),
        )

    console.print(table)
