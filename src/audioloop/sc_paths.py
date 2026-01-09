"""SuperCollider installation path discovery and validation."""

import os
from pathlib import Path


# Default SuperCollider application path on macOS
SC_APP_PATH = Path("/Applications/SuperCollider.app")


def get_sc_app_path() -> Path:
    """Get the SuperCollider application path.

    Checks AUDIOLOOP_SC_APP environment variable first, falls back to default.

    Returns:
        Path to SuperCollider.app directory.
    """
    env_path = os.environ.get("AUDIOLOOP_SC_APP")
    if env_path:
        return Path(env_path)
    return SC_APP_PATH


def get_sclang_path() -> Path:
    """Get the path to the sclang executable.

    Returns:
        Path to sclang executable.
    """
    return get_sc_app_path() / "Contents" / "MacOS" / "sclang"


def get_scsynth_path() -> Path:
    """Get the path to the scsynth executable.

    Returns:
        Path to scsynth executable.
    """
    return get_sc_app_path() / "Contents" / "Resources" / "scsynth"


def get_sclang_dir() -> Path:
    """Get the directory containing sclang.

    This is needed as the working directory when running sclang,
    as sclang requires Qt/Cocoa resources to be relative to this directory.

    Returns:
        Path to the directory containing sclang.
    """
    return get_sclang_path().parent


def validate_sc_installation() -> tuple[bool, str | None]:
    """Validate that SuperCollider is installed and accessible.

    Returns:
        Tuple of (is_valid, error_message).
        If valid, returns (True, None).
        If invalid, returns (False, helpful_error_message).
    """
    sc_app = get_sc_app_path()
    sclang = get_sclang_path()
    scsynth = get_scsynth_path()

    if not sc_app.exists():
        return False, (
            f"SuperCollider not found at {sc_app}\n\n"
            "To install SuperCollider:\n"
            "  1. Download from https://supercollider.github.io/downloads\n"
            "  2. Move SuperCollider.app to /Applications\n\n"
            "Or set AUDIOLOOP_SC_APP environment variable to a custom location:\n"
            "  export AUDIOLOOP_SC_APP=/path/to/SuperCollider.app"
        )

    if not sclang.exists():
        return False, (
            f"sclang executable not found at {sclang}\n\n"
            "The SuperCollider installation may be corrupted.\n"
            "Try reinstalling SuperCollider from https://supercollider.github.io/downloads"
        )

    if not scsynth.exists():
        return False, (
            f"scsynth executable not found at {scsynth}\n\n"
            "The SuperCollider installation may be corrupted.\n"
            "Try reinstalling SuperCollider from https://supercollider.github.io/downloads"
        )

    # Check if sclang is executable
    if not os.access(sclang, os.X_OK):
        return False, (
            f"sclang is not executable: {sclang}\n\n"
            "Try running:\n"
            f"  chmod +x {sclang}"
        )

    return True, None


def require_sc_installation() -> None:
    """Validate SC installation and raise if not found.

    Raises:
        RuntimeError: If SuperCollider is not properly installed.
    """
    is_valid, error = validate_sc_installation()
    if not is_valid:
        raise RuntimeError(error)
