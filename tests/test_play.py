"""Tests for the play command."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from audioloop.play import play_audio, PlaybackError


# Use the test fixture created for CLI tests
FIXTURE_PATH = Path(__file__).parent / "fixtures" / "test_tone.wav"


class TestPlayAudioFunction:
    """Tests for the play_audio function."""

    def test_play_existing_file(self):
        """Verify afplay is called with correct arguments."""
        with patch("audioloop.play.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")

            play_audio(FIXTURE_PATH)

            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert call_args[0] == "afplay"
            assert str(FIXTURE_PATH) in call_args[1]

    def test_play_nonexistent_file(self):
        """Verify FileNotFoundError raised for nonexistent file."""
        with pytest.raises(FileNotFoundError) as exc_info:
            play_audio(Path("nonexistent_file.wav"))

        assert "not found" in str(exc_info.value).lower()

    def test_play_directory_not_file(self, tmp_path):
        """Verify FileNotFoundError raised when path is a directory."""
        with pytest.raises(FileNotFoundError) as exc_info:
            play_audio(tmp_path)

        assert "not a file" in str(exc_info.value).lower()

    def test_play_afplay_error(self):
        """Verify PlaybackError raised when afplay fails."""
        with patch("audioloop.play.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stderr="Audio error")

            with pytest.raises(PlaybackError) as exc_info:
                play_audio(FIXTURE_PATH)

            assert "playback failed" in str(exc_info.value).lower()


class TestPlayCLI:
    """CLI integration tests for the play command."""

    def test_play_cli_output(self):
        """Verify 'Playing:' and 'Played:' messages in CLI output."""
        from typer.testing import CliRunner
        from audioloop.cli import app

        # Mock subprocess at the module level to prevent actual playback
        with patch("audioloop.play.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")

            runner = CliRunner()
            result = runner.invoke(app, ["play", str(FIXTURE_PATH)])

            assert result.exit_code == 0
            assert "Playing:" in result.stdout
            assert "Played:" in result.stdout
            assert str(FIXTURE_PATH) in result.stdout

    def test_play_nonexistent_file_exit_code(self):
        """Verify exit code 2 for nonexistent file."""
        result = subprocess.run(
            ["uv", "run", "audioloop", "play", "nonexistent_file.wav"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 2
        assert "not found" in result.stderr.lower() or "not found" in result.stdout.lower()

    def test_play_directory_exit_code(self, tmp_path):
        """Verify exit code 2 when path is a directory."""
        result = subprocess.run(
            ["uv", "run", "audioloop", "play", str(tmp_path)],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 2

    def test_play_help(self):
        """Verify play command appears in help output."""
        result = subprocess.run(
            ["uv", "run", "audioloop", "--help"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "play" in result.stdout.lower()
        assert "audio" in result.stdout.lower()
