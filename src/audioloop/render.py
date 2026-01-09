"""Render SuperCollider code to WAV files."""

import tempfile
import time
import wave
from dataclasses import dataclass
from pathlib import Path

from audioloop.errors import SCError, has_error, extract_error
from audioloop.sclang import run_sclang
from audioloop.wrapper import needs_wrapping, wrap_function, replace_placeholders


@dataclass
class RenderResult:
    """Result of a render operation."""

    success: bool
    output_path: Path | None
    duration_sec: float | None
    render_time_sec: float
    error: SCError | None
    sclang_output: str
    mode: str  # "full_nrt" or "wrapped"


def get_wav_duration(path: Path) -> float | None:
    """Get the duration of a WAV file in seconds.

    Args:
        path: Path to the WAV file.

    Returns:
        Duration in seconds, or None if file cannot be read.
    """
    try:
        with wave.open(str(path), "rb") as wav:
            frames = wav.getnframes()
            rate = wav.getframerate()
            return frames / rate
    except Exception:
        return None


def render(
    input_path: Path,
    output_path: Path,
    timeout: float = 120.0,
    duration: float | None = None,
) -> RenderResult:
    """Render SuperCollider code to a WAV file.

    Supports two modes:
    - Full NRT mode: Input contains recordNRT call with __OUTPUT_PATH__ placeholder
    - Wrapped mode: Input is a simple function, wrapped in NRT boilerplate

    Args:
        input_path: Path to the .scd file to render.
        output_path: Path where the WAV file will be written.
        timeout: Maximum time in seconds to wait for rendering.
        duration: Duration in seconds (required for wrapped mode, ignored for full NRT).

    Returns:
        RenderResult with render outcome and details.
    """
    start_time = time.time()

    # Convert output path to absolute - sclang runs with cwd set to SC app directory,
    # so relative paths would resolve incorrectly
    output_path = output_path.resolve()

    # Validate input file exists
    if not input_path.exists():
        return RenderResult(
            success=False,
            output_path=None,
            duration_sec=None,
            render_time_sec=time.time() - start_time,
            error=SCError(message=f"Input file not found: {input_path}"),
            sclang_output="",
            mode="unknown",
        )

    # Read input file
    try:
        content = input_path.read_text()
    except Exception as e:
        return RenderResult(
            success=False,
            output_path=None,
            duration_sec=None,
            render_time_sec=time.time() - start_time,
            error=SCError(message=f"Failed to read input file: {e}"),
            sclang_output="",
            mode="unknown",
        )

    # Detect mode
    if needs_wrapping(content):
        mode = "wrapped"
        # Duration is required for wrapped mode
        if duration is None:
            return RenderResult(
                success=False,
                output_path=None,
                duration_sec=None,
                render_time_sec=time.time() - start_time,
                error=SCError(
                    message="Duration required for simple function syntax. Use --duration flag."
                ),
                sclang_output="",
                mode=mode,
            )
        # Wrap the function
        prepared_code = wrap_function(content, duration, output_path)
    else:
        mode = "full_nrt"
        # Replace output path placeholder
        prepared_code = replace_placeholders(content, output_path, duration)

    # Write prepared script to temp file
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".scd", delete=False
    ) as temp_file:
        temp_file.write(prepared_code)
        temp_path = Path(temp_file.name)

    try:
        # Run sclang
        result = run_sclang(temp_path, timeout=timeout)

        # Check for timeout
        if result.timed_out:
            # Check if there's an error in the partial output (compilation errors
            # cause sclang to hang in SC 3.14.x, so we may have error info)
            if has_error(result.stdout):
                error = extract_error(result.stdout)
            else:
                error = SCError(
                    message=f"Render timed out after {timeout} seconds. "
                    "This may indicate a compilation error or infinite loop."
                )
            return RenderResult(
                success=False,
                output_path=None,
                duration_sec=None,
                render_time_sec=time.time() - start_time,
                error=error,
                sclang_output=result.stdout,
                mode=mode,
            )

        # Check for errors in output
        if has_error(result.stdout):
            error = extract_error(result.stdout)
            return RenderResult(
                success=False,
                output_path=None,
                duration_sec=None,
                render_time_sec=time.time() - start_time,
                error=error or SCError(message="Unknown error in sclang output"),
                sclang_output=result.stdout,
                mode=mode,
            )

        # Verify output file exists and has content
        if not output_path.exists():
            return RenderResult(
                success=False,
                output_path=None,
                duration_sec=None,
                render_time_sec=time.time() - start_time,
                error=SCError(message="Output file was not created"),
                sclang_output=result.stdout,
                mode=mode,
            )

        if output_path.stat().st_size == 0:
            return RenderResult(
                success=False,
                output_path=None,
                duration_sec=None,
                render_time_sec=time.time() - start_time,
                error=SCError(message="Output file is empty"),
                sclang_output=result.stdout,
                mode=mode,
            )

        # Get duration from output file
        wav_duration = get_wav_duration(output_path)

        return RenderResult(
            success=True,
            output_path=output_path,
            duration_sec=wav_duration,
            render_time_sec=time.time() - start_time,
            error=None,
            sclang_output=result.stdout,
            mode=mode,
        )

    finally:
        # Clean up temp file
        try:
            temp_path.unlink()
        except Exception:
            pass
