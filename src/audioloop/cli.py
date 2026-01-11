"""CLI entry point for audioloop."""

import json
import tempfile
import time
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from audioloop import __version__
from audioloop.analyze import analyze as do_analyze, AnalysisError
from audioloop.compare import compare_audio, print_comparison_human
from audioloop.errors import format_error_human
from audioloop.interpret import format_analysis_human
from audioloop.play import play_audio, PlaybackError
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
    no_psychoacoustic: bool = typer.Option(
        False,
        "--no-psychoacoustic",
        help="Skip psychoacoustic metrics (faster analysis)",
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
        result = do_analyze(file, skip_psychoacoustic=no_psychoacoustic)
    except AnalysisError as e:
        error_console.print(f"[red]Analysis failed:[/red] {e}")
        raise typer.Exit(1)  # Analysis error

    # Output results
    if json_output:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        console.print(format_analysis_human(result))


@app.command()
def play(
    file: Path = typer.Argument(
        ...,
        help="Audio file to play (WAV)",
        exists=False,  # We handle existence check ourselves for better error messages
    ),
) -> None:
    """Play an audio file through the system speaker.

    Uses macOS afplay for playback. Blocks until playback completes.
    Press Ctrl+C to stop playback.

    Examples:

        audioloop play output.wav

        audioloop play tests/fixtures/test_tone.wav
    """
    # Validate file exists
    if not file.exists():
        error_console.print(f"[red]Error:[/red] File not found: {file}")
        raise typer.Exit(2)  # System error

    if not file.is_file():
        error_console.print(f"[red]Error:[/red] Not a file: {file}")
        raise typer.Exit(2)  # System error

    # Play audio
    console.print(f"Playing: {file}")
    try:
        play_audio(file)
    except PlaybackError as e:
        error_console.print(f"[red]Playback error:[/red] {e}")
        raise typer.Exit(1)

    console.print(f"Played: {file}")


@app.command()
def compare(
    file_a: Path = typer.Argument(
        ...,
        help="First audio file (baseline)",
        exists=False,  # We handle existence check ourselves
    ),
    file_b: Path = typer.Argument(
        ...,
        help="Second audio file (comparison)",
        exists=False,  # We handle existence check ourselves
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        "-j",
        help="Output as JSON",
    ),
) -> None:
    """Compare two audio files and show feature deltas.

    Computes feature-by-feature differences between two audio files,
    highlighting significant changes (>10%) with interpretive context.

    Examples:

        audioloop compare iteration-1.wav iteration-2.wav

        audioloop compare before.wav after.wav --json
    """
    # Validate both files exist
    if not file_a.exists():
        error_console.print(f"[red]Error:[/red] File not found: {file_a}")
        raise typer.Exit(2)  # System error

    if not file_a.is_file():
        error_console.print(f"[red]Error:[/red] Not a file: {file_a}")
        raise typer.Exit(2)  # System error

    if not file_b.exists():
        error_console.print(f"[red]Error:[/red] File not found: {file_b}")
        raise typer.Exit(2)  # System error

    if not file_b.is_file():
        error_console.print(f"[red]Error:[/red] Not a file: {file_b}")
        raise typer.Exit(2)  # System error

    # Run comparison
    try:
        result = compare_audio(file_a, file_b)
    except AnalysisError as e:
        error_console.print(f"[red]Comparison failed:[/red] {e}")
        raise typer.Exit(1)  # Analysis error

    # Output results
    if json_output:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print_comparison_human(result, console)


# Counter for iterate output files
_iterate_counter = 0


@app.command()
def iterate(
    source: str = typer.Argument(
        ...,
        help="SuperCollider file path OR inline SC code (with --code flag)",
    ),
    code: bool = typer.Option(
        False,
        "--code",
        "-c",
        help="Treat source as inline SC code instead of file path",
    ),
    duration: Optional[float] = typer.Option(
        None,
        "--duration",
        "-d",
        help="Duration in seconds (required for inline code or simple function files)",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output WAV path. Default: temp file (cleaned up) or iterate_NNN.wav with --keep",
    ),
    keep: bool = typer.Option(
        False,
        "--keep",
        "-k",
        help="Keep WAV file after iterate completes",
    ),
    no_play: bool = typer.Option(
        False,
        "--no-play",
        help="Skip playback (for automated iteration)",
    ),
    no_psychoacoustic: bool = typer.Option(
        False,
        "--no-psychoacoustic",
        help="Skip psychoacoustic metrics (faster analysis)",
    ),
    json_output: bool = typer.Option(
        True,  # Default to JSON since Claude is primary user
        "--json",
        "-j",
        help="Output as JSON (default for this command)",
    ),
    human: bool = typer.Option(
        False,
        "--human",
        "-h",
        help="Use human-readable output instead of JSON",
    ),
) -> None:
    """Render, analyze, and optionally play SuperCollider code in one command.

    Combines render→analyze→play into a single invocation for fast iteration.
    Accepts inline SC code or file paths.

    Examples:

        # Inline code (requires --code and --duration)
        audioloop iterate --code -d 2 "{ SinOsc.ar(440) * 0.3 ! 2 }"

        # File path
        audioloop iterate my_sound.scd -d 2

        # Skip playback for automated workflows
        audioloop iterate --code -d 1 "{ Saw.ar(200) * 0.3 ! 2 }" --no-play

        # Keep the rendered WAV file
        audioloop iterate --code -d 2 "{ Pulse.ar(300) * 0.3 ! 2 }" --keep
    """
    global _iterate_counter
    total_start = time.time()

    # Determine actual output format
    use_json = json_output and not human

    # Validate: --code requires --duration
    if code and duration is None:
        output_data = {
            "success": False,
            "error": "Duration required for inline code. Use --duration/-d flag.",
            "render": None,
            "analysis": None,
            "played": False,
            "output_path": None,
            "total_time_sec": round(time.time() - total_start, 3),
        }
        if use_json:
            print(json.dumps(output_data, indent=2))
        else:
            error_console.print("[red]Error:[/red] Duration required for inline code. Use --duration/-d flag.")
        raise typer.Exit(2)

    # Determine input path
    temp_scd = None
    if code:
        # Write inline code to temp file
        temp_scd = tempfile.NamedTemporaryFile(
            mode="w", suffix=".scd", delete=False
        )
        temp_scd.write(source)
        temp_scd.close()
        input_path = Path(temp_scd.name)
    else:
        input_path = Path(source)
        # Validate file exists
        if not input_path.exists():
            output_data = {
                "success": False,
                "error": f"File not found: {source}",
                "render": None,
                "analysis": None,
                "played": False,
                "output_path": None,
                "total_time_sec": round(time.time() - total_start, 3),
            }
            if use_json:
                print(json.dumps(output_data, indent=2))
            else:
                error_console.print(f"[red]Error:[/red] File not found: {source}")
            raise typer.Exit(2)

    # Determine output path
    temp_wav = None
    if output is not None:
        output_path = output
    elif keep:
        # Generate iterate_NNN.wav
        _iterate_counter += 1
        output_path = Path(f"iterate_{_iterate_counter:03d}.wav")
        while output_path.exists():
            _iterate_counter += 1
            output_path = Path(f"iterate_{_iterate_counter:03d}.wav")
    else:
        # Use temp file
        temp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        temp_wav.close()
        output_path = Path(temp_wav.name)

    try:
        # Step 1: Render
        render_result = do_render(
            input_path=input_path,
            output_path=output_path,
            duration=duration,
        )

        render_data = {
            "success": render_result.success,
            "output_path": str(render_result.output_path) if render_result.output_path else None,
            "duration_sec": render_result.duration_sec,
            "render_time_sec": round(render_result.render_time_sec, 3),
            "mode": render_result.mode,
        }
        if render_result.error:
            render_data["error"] = {
                "message": render_result.error.message,
                "file": render_result.error.file,
                "line": render_result.error.line,
                "char": render_result.error.char,
            }

        if not render_result.success:
            output_data = {
                "success": False,
                "render": render_data,
                "analysis": None,
                "played": False,
                "output_path": None,
                "total_time_sec": round(time.time() - total_start, 3),
            }
            if use_json:
                print(json.dumps(output_data, indent=2))
            else:
                error_console.print("[red]Render failed[/red]")
                if render_result.error:
                    error_console.print(format_error_human(render_result.error))
            raise typer.Exit(1)

        # Step 2: Analyze
        analysis_data = None
        try:
            analysis_result = do_analyze(output_path, skip_psychoacoustic=no_psychoacoustic)
            analysis_data = analysis_result.to_dict()
        except AnalysisError as e:
            output_data = {
                "success": False,
                "render": render_data,
                "analysis": {"error": str(e)},
                "played": False,
                "output_path": str(output_path) if keep or output else None,
                "total_time_sec": round(time.time() - total_start, 3),
            }
            if use_json:
                print(json.dumps(output_data, indent=2))
            else:
                console.print(f"[green]Rendered:[/green] {output_path}")
                error_console.print(f"[red]Analysis failed:[/red] {e}")
            raise typer.Exit(1)

        # Step 3: Play (if not skipped)
        played = False
        play_error = None
        if not no_play:
            try:
                if not use_json:
                    console.print(f"Playing: {output_path}")
                play_audio(output_path)
                played = True
            except PlaybackError as e:
                play_error = str(e)

        # Build success output
        final_output_path = str(output_path) if (keep or output) else None
        output_data = {
            "success": True,
            "render": render_data,
            "analysis": analysis_data,
            "played": played,
            "output_path": final_output_path,
            "total_time_sec": round(time.time() - total_start, 3),
        }
        if play_error:
            output_data["play_error"] = play_error

        if use_json:
            print(json.dumps(output_data, indent=2))
        else:
            console.print(f"[green]✓ Rendered:[/green] {output_path} ({render_result.duration_sec:.2f}s)")
            if played:
                console.print("[green]✓ Played[/green]")
            elif play_error:
                error_console.print(f"[yellow]⚠ Playback failed:[/yellow] {play_error}")
            console.print()
            console.print(format_analysis_human(analysis_result))

    finally:
        # Cleanup temp files
        if temp_scd is not None:
            try:
                Path(temp_scd.name).unlink()
            except Exception:
                pass
        if temp_wav is not None and not keep and output is None:
            try:
                Path(temp_wav.name).unlink()
            except Exception:
                pass
