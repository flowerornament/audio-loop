"""sclang subprocess execution with proper environment setup."""

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from audioloop.sc_paths import get_sclang_path, get_sclang_dir, validate_sc_installation


@dataclass
class SclangResult:
    """Result of running sclang."""

    success: bool
    stdout: str
    stderr: str
    exit_code: int
    timed_out: bool


def run_sclang(script_path: Path, timeout: float = 60.0) -> SclangResult:
    """Execute a SuperCollider script with sclang.

    Runs sclang with proper environment setup:
    - Sets cwd to sclang's directory (required for Qt/Cocoa on macOS)
    - On Linux: Sets QT_QPA_PLATFORM=offscreen for headless operation
    - Captures stdout/stderr
    - Handles timeout

    Args:
        script_path: Path to the .scd file to execute.
        timeout: Maximum time in seconds to wait for completion.

    Returns:
        SclangResult with execution details.

    Raises:
        RuntimeError: If SuperCollider is not installed.
        FileNotFoundError: If script_path doesn't exist.
        PermissionError: If sclang is not executable.
    """
    # Validate inputs
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")

    # Validate SC installation
    is_valid, error = validate_sc_installation()
    if not is_valid:
        raise RuntimeError(error)

    sclang_path = get_sclang_path()
    sclang_dir = get_sclang_dir()

    # Set up environment
    env = os.environ.copy()
    # On Linux, use offscreen Qt platform for headless operation
    # On macOS, the cocoa platform works without display (offscreen not available)
    if sys.platform == "linux":
        env["QT_QPA_PLATFORM"] = "offscreen"

    try:
        result = subprocess.run(
            [str(sclang_path), str(script_path)],
            cwd=str(sclang_dir),
            capture_output=True,
            timeout=timeout,
            text=True,
            env=env,
        )

        return SclangResult(
            success=result.returncode == 0,
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.returncode,
            timed_out=False,
        )

    except subprocess.TimeoutExpired as e:
        # On timeout, return partial output if available
        stdout = e.stdout.decode("utf-8", errors="replace") if e.stdout else ""
        stderr = e.stderr.decode("utf-8", errors="replace") if e.stderr else ""

        return SclangResult(
            success=False,
            stdout=stdout,
            stderr=stderr,
            exit_code=-1,
            timed_out=True,
        )

    except PermissionError:
        raise PermissionError(
            f"Permission denied running sclang: {sclang_path}\n\n"
            f"Try running:\n  chmod +x {sclang_path}"
        )
