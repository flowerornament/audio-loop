"""Audio playback module for audioloop."""

import subprocess
from pathlib import Path


class PlaybackError(Exception):
    """Raised when audio playback fails."""

    pass


def play_audio(file_path: Path) -> None:
    """Play an audio file using the system audio player.

    Uses afplay on macOS. Blocks until playback completes.
    User can interrupt with Ctrl+C.

    Args:
        file_path: Path to the audio file to play.

    Raises:
        FileNotFoundError: If the file does not exist.
        PlaybackError: If playback fails for any other reason.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if not file_path.is_file():
        raise FileNotFoundError(f"Not a file: {file_path}")

    try:
        result = subprocess.run(
            ["afplay", str(file_path)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            raise PlaybackError(f"Playback failed: {error_msg}")
    except FileNotFoundError:
        raise PlaybackError("afplay not found - this command requires macOS")
    except subprocess.SubprocessError as e:
        raise PlaybackError(f"Playback failed: {e}")
