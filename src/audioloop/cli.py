"""CLI entry point for audioloop."""

import json
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from audioloop import __version__
from audioloop.analyze import analyze as do_analyze, AnalysisError
from audioloop.errors import format_error_human
from audioloop.interpret import format_analysis_human
from audioloop.render import render as do_render

app = typer.Typer(
    name="audioloop",
    help="CLI tool for rendering SuperCollider code to WAV files.",
    no_args_is_help=True,
)

console = Console()
error_console = Console(stderr=True)


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


@app.command()
def render(
    file: Path = typer.Argument(
        ...,
        help="SuperCollider file to render (.scd)",
        exists=False,  # We handle existence check ourselves for better error messages
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output WAV path. Defaults to input filename with .wav extension.",
    ),
    duration: Optional[float] = typer.Option(
        None,
        "--duration",
        "-d",
        help="Duration in seconds (required for simple function syntax).",
    ),
    timeout: float = typer.Option(
        120.0,
        "--timeout",
        "-t",
        help="Timeout in seconds for rendering.",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output result as JSON.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        help="Show sclang output.",
    ),
) -> None:
    """Render SuperCollider code to a WAV file.

    Supports two modes:

    1. Full NRT mode: Your .scd file contains a complete NRT script with
       Score.recordNRT() and a __OUTPUT_PATH__ placeholder.

    2. Simple function mode: Your .scd file contains just a function like
       { SinOsc.ar(440) }. Use --duration to specify render length.

    Examples:

        audioloop render full_nrt.scd -o output.wav

        audioloop render simple.scd --duration 2 -o output.wav
    """
    # Determine output path
    if output is None:
        output = file.with_suffix(".wav")

    # Ensure output directory exists (but only if it's a valid path)
    # Skip this if the input file doesn't exist - we'll get a cleaner error from render()
    if file.exists():
        try:
            output.parent.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass  # Let render() handle path issues

    # Do the render
    result = do_render(
        input_path=file,
        output_path=output,
        timeout=timeout,
        duration=duration,
    )

    # Output results
    if json_output:
        output_data = {
            "success": result.success,
            "output_path": str(result.output_path) if result.output_path else None,
            "duration_sec": result.duration_sec,
            "render_time_sec": round(result.render_time_sec, 3),
            "mode": result.mode,
        }
        if result.error:
            output_data["error"] = {
                "message": result.error.message,
                "file": result.error.file,
                "line": result.error.line,
                "char": result.error.char,
            }
        if verbose:
            output_data["sclang_output"] = result.sclang_output
        print(json.dumps(output_data, indent=2))
    else:
        # Human-readable output
        if result.success:
            console.print(f"[green]Rendered:[/green] {result.output_path}")
            if result.duration_sec:
                console.print(
                    f"  Duration: {result.duration_sec:.2f}s, "
                    f"Render time: {result.render_time_sec:.2f}s"
                )
            console.print(f"  Mode: {result.mode}")
        else:
            error_console.print("[red]Render failed[/red]")
            if result.error:
                error_console.print(format_error_human(result.error))

        if verbose and result.sclang_output:
            console.print("\n[dim]--- sclang output ---[/dim]")
            console.print(result.sclang_output)

    # Exit with appropriate code
    if not result.success:
        # Exit code 1 for SC errors (syntax, runtime), 2 for system errors
        # SC errors have sclang output; system errors (file not found, missing
        # --duration, SC not installed) occur before sclang runs
        if result.sclang_output:
            raise typer.Exit(1)  # SC error
        else:
            raise typer.Exit(2)  # System error


@app.command()
def analyze(
    file: Path = typer.Argument(
        ...,
        help="WAV file to analyze",
        exists=False,  # We handle existence check ourselves for better error messages
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output as JSON",
    ),
) -> None:
    """Analyze an audio file and extract acoustic features.

    Extracts spectral, temporal, stereo, and loudness features from a WAV file.
    Outputs human-readable summary by default, or JSON with --json flag.

    Examples:

        audioloop analyze recording.wav

        audioloop analyze recording.wav --json
    """
    # Validate file exists
    if not file.exists():
        error_console.print(f"[red]Error:[/red] File not found: {file}")
        raise typer.Exit(2)  # System error

    if not file.is_file():
        error_console.print(f"[red]Error:[/red] Not a file: {file}")
        raise typer.Exit(2)  # System error

    # Run analysis
    try:
        result = do_analyze(file)
    except AnalysisError as e:
        error_console.print(f"[red]Analysis failed:[/red] {e}")
        raise typer.Exit(1)  # Analysis error

    # Output results
    if json_output:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        console.print(format_analysis_human(result))
