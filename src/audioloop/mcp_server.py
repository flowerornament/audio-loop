"""MCP server for audioloop CLI tools.

Exposes audioloop analysis and rendering capabilities as MCP tools.
Uses FastMCP for automatic schema generation and protocol handling.
"""

import asyncio
import json
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from audioloop import __version__
from audioloop.mcp_models import (
    AnalysisResult,
    ComparisonResult,
    IterateResult,
    RenderResult,
)

# Configure logging to stderr (stdout is reserved for MCP protocol)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("audioloop.mcp")


async def run_cli(args: list[str]) -> str:
    """Run audioloop CLI command asynchronously.

    Args:
        args: Command arguments to pass to audioloop CLI.

    Returns:
        stdout from the command.

    Raises:
        RuntimeError: If command fails with non-zero exit code.
    """
    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "audioloop",
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()

    if proc.returncode != 0:
        error_msg = stderr.decode().strip() if stderr else "Unknown error"
        raise RuntimeError(f"audioloop failed: {error_msg}")

    return stdout.decode()


@asynccontextmanager
async def app_lifespan(server: FastMCP):
    """Verify audioloop CLI is available on startup."""
    logger.info("Starting audioloop MCP server...")

    # Verify audioloop is installed and accessible
    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            "-m",
            "audioloop",
            "--version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()

        if proc.returncode != 0:
            raise RuntimeError("audioloop CLI not available")

        version = stdout.decode().strip()
        logger.info(f"audioloop CLI ready: {version}")
    except FileNotFoundError:
        raise RuntimeError("Python executable not found")

    yield

    logger.info("Shutting down audioloop MCP server")


# Create FastMCP server instance
mcp = FastMCP("audioloop", lifespan=app_lifespan)


@mcp.tool()
async def version() -> dict:
    """Get audioloop version information.

    Returns:
        Version info including audioloop and MCP server versions.
    """
    return {
        "audioloop": __version__,
        "mcp_server": "0.1.0",
        "status": "ready",
    }


@mcp.tool()
async def render(
    file_path: str,
    duration: float | None = None,
    output: str | None = None,
) -> RenderResult:
    """Render SuperCollider code to a WAV file.

    Supports two modes:
    1. NRT mode: Your .scd file contains a complete NRT script with Score.recordNRT()
       and a __OUTPUT_PATH__ placeholder.
    2. Simple function mode: Your .scd file contains just a function like { SinOsc.ar(440) }.
       Use duration to specify render length.

    Args:
        file_path: Path to SuperCollider .scd file to render.
        duration: Duration in seconds (required for simple function syntax).
        output: Output WAV path. Defaults to input filename with .wav extension.

    Returns:
        RenderResult with success status, output path, duration, and timing info.
    """
    # Resolve to absolute path
    abs_path = Path(file_path).resolve()

    # Build command
    args = ["render", str(abs_path), "--json"]
    if duration is not None:
        args.extend(["--duration", str(duration)])
    if output is not None:
        args.extend(["-o", str(Path(output).resolve())])

    # Run CLI
    stdout = await run_cli(args)

    # Parse JSON and construct model
    data = json.loads(stdout)
    return RenderResult.model_validate(data)


@mcp.tool()
async def analyze(
    file_path: str,
    no_psychoacoustic: bool = False,
    spectrogram_path: str | None = None,
) -> AnalysisResult:
    """Analyze an audio file and extract acoustic features.

    Extracts spectral, temporal, stereo, loudness, and optionally psychoacoustic
    features from a WAV file.

    Args:
        file_path: Path to WAV file to analyze.
        no_psychoacoustic: Skip psychoacoustic metrics for faster analysis.
        spectrogram_path: Path to save spectrogram PNG. The path will be included
            in the result's spectrogram_path field.

    Returns:
        AnalysisResult with all extracted features. If spectrogram_path was provided,
        the spectrogram_path field will contain the path to the generated PNG.
    """
    # Resolve to absolute path
    abs_path = Path(file_path).resolve()

    # Build command
    args = ["analyze", str(abs_path), "--json"]
    if no_psychoacoustic:
        args.append("--no-psychoacoustic")
    if spectrogram_path is not None:
        spec_abs = Path(spectrogram_path).resolve()
        args.extend(["--spectrogram", str(spec_abs)])

    # Run CLI
    stdout = await run_cli(args)

    # Parse JSON and construct model
    data = json.loads(stdout)
    return AnalysisResult.model_validate(data)


@mcp.tool()
async def play(file_path: str) -> dict:
    """Play an audio file through the system speaker.

    Uses macOS afplay for playback. This blocks until playback completes.
    Useful for listening to rendered audio during iteration.

    Args:
        file_path: Path to WAV file to play.

    Returns:
        Dict with success status.
    """
    # Resolve to absolute path
    abs_path = Path(file_path).resolve()

    # play command doesn't have JSON output, just run it
    args = ["play", str(abs_path)]

    try:
        await run_cli(args)
        return {"success": True, "file": str(abs_path)}
    except RuntimeError as e:
        return {"success": False, "file": str(abs_path), "error": str(e)}


@mcp.tool()
async def iterate(
    source: str,
    code: bool = False,
    duration: float | None = None,
    keep: bool = False,
    no_play: bool = False,
    no_psychoacoustic: bool = False,
    spectrogram_path: str | None = None,
) -> IterateResult:
    """Render, analyze, and optionally play SuperCollider code in one command.

    This is the primary workflow tool for Claude to iterate on audio generation.
    Combines render → analyze → play into a single invocation for fast feedback.

    Accepts either a file path to a .scd file, or inline SuperCollider code
    when code=True.

    Args:
        source: Path to SuperCollider .scd file, or inline SC code if code=True.
        code: If True, treat source as inline SC code instead of file path.
        duration: Duration in seconds (required for inline code or simple functions).
        keep: Keep the rendered WAV file after iterate completes.
        no_play: Skip audio playback (useful for automated iteration).
        no_psychoacoustic: Skip psychoacoustic metrics for faster analysis.
        spectrogram_path: Path to save spectrogram PNG.

    Returns:
        IterateResult with render info, analysis data, and playback status.
        If render fails, includes error details from SuperCollider.
    """
    # Build command
    args = ["iterate"]

    if code:
        args.append("--code")

    args.append(source if code else str(Path(source).resolve()))
    args.append("--json")

    if duration is not None:
        args.extend(["--duration", str(duration)])
    if keep:
        args.append("--keep")
    if no_play:
        args.append("--no-play")
    if no_psychoacoustic:
        args.append("--no-psychoacoustic")
    if spectrogram_path is not None:
        spec_abs = Path(spectrogram_path).resolve()
        args.extend(["--spectrogram", str(spec_abs)])

    # Run CLI - iterate can fail in various ways, handle gracefully
    try:
        stdout = await run_cli(args)
        data = json.loads(stdout)
        return IterateResult.model_validate(data)
    except RuntimeError as e:
        # CLI failed - return an error result
        return IterateResult(
            success=False,
            render=None,
            analysis=None,
            played=False,
            output_path=None,
            total_time_sec=0.0,
            error=str(e),
        )


@mcp.tool()
async def compare(
    file_a: str,
    file_b: str,
) -> ComparisonResult:
    """Compare two audio files and show feature deltas.

    Computes feature-by-feature differences between two audio files,
    highlighting significant changes (>10%) with interpretive context.
    Useful for A/B comparison when iterating on sound design.

    Args:
        file_a: Path to baseline audio file (WAV).
        file_b: Path to comparison audio file (WAV).

    Returns:
        ComparisonResult with per-metric deltas and a summary of significant changes.
    """
    # Resolve to absolute paths
    abs_a = Path(file_a).resolve()
    abs_b = Path(file_b).resolve()

    # Build command
    args = ["compare", str(abs_a), str(abs_b), "--json"]

    # Run CLI
    stdout = await run_cli(args)

    # Parse JSON and construct model
    data = json.loads(stdout)
    return ComparisonResult.model_validate(data)


if __name__ == "__main__":
    mcp.run()
