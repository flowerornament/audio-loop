"""CLI entry point for audioloop."""

import typer

from audioloop import __version__

app = typer.Typer(
    name="audioloop",
    help="CLI tool for rendering SuperCollider code to WAV files.",
    no_args_is_help=True,
)


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        print(f"audioloop {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """audioloop - CLI tool for rendering SuperCollider code to WAV files."""
    pass
