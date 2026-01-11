"""CLI integration tests for the iterate command."""

import json
import subprocess
from pathlib import Path

import pytest


# Use existing test fixtures
FIXTURE_PATH = Path(__file__).parent / "fixtures"
SIMPLE_FUNCTION = FIXTURE_PATH / "simple_function.scd"
TEST_TONE = FIXTURE_PATH / "test_tone.wav"


class TestIterateInlineCode:
    """Tests for inline code mode with --code flag."""

    def test_inline_code_success(self):
        """Inline code with --code and --duration renders and analyzes successfully."""
        result = subprocess.run(
            [
                "uv", "run", "audioloop", "iterate",
                "--code", "-d", "1",
                "{ SinOsc.ar(440) * 0.3 ! 2 }",
                "--json", "--no-play"
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        assert result.returncode == 0, f"Command failed: {result.stderr}"

        data = json.loads(result.stdout)
        assert data["success"] is True
        assert data["render"]["success"] is True
        assert data["analysis"] is not None
        assert data["played"] is False
        assert "spectral" in data["analysis"]
        assert "temporal" in data["analysis"]

    def test_inline_code_missing_duration(self):
        """Inline code without --duration returns error with exit code 2."""
        result = subprocess.run(
            [
                "uv", "run", "audioloop", "iterate",
                "--code",
                "{ SinOsc.ar(440) * 0.3 ! 2 }",
                "--json", "--no-play"
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 2

        data = json.loads(result.stdout)
        assert data["success"] is False
        assert "Duration required" in data["error"]
        assert data["render"] is None
        assert data["analysis"] is None


class TestIterateFileMode:
    """Tests for file path mode."""

    def test_file_mode_success(self):
        """Existing simple function file renders and analyzes successfully."""
        result = subprocess.run(
            [
                "uv", "run", "audioloop", "iterate",
                str(SIMPLE_FUNCTION),
                "-d", "1",
                "--json", "--no-play"
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        assert result.returncode == 0, f"Command failed: {result.stderr}"

        data = json.loads(result.stdout)
        assert data["success"] is True
        assert data["render"]["success"] is True
        assert data["render"]["mode"] == "wrapped"
        assert data["analysis"] is not None

    def test_file_not_found(self):
        """Non-existent file returns error with exit code 2."""
        result = subprocess.run(
            [
                "uv", "run", "audioloop", "iterate",
                "nonexistent_file.scd",
                "-d", "1",
                "--json", "--no-play"
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 2

        data = json.loads(result.stdout)
        assert data["success"] is False
        assert "not found" in data["error"].lower() or "File not found" in data["error"]


class TestIterateOptions:
    """Tests for command options."""

    def test_no_play_skips_playback(self):
        """--no-play flag results in played=false."""
        result = subprocess.run(
            [
                "uv", "run", "audioloop", "iterate",
                "--code", "-d", "1",
                "{ SinOsc.ar(440) * 0.3 ! 2 }",
                "--json", "--no-play"
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        data = json.loads(result.stdout)
        assert data["played"] is False

    def test_no_psychoacoustic_excludes_metrics(self):
        """--no-psychoacoustic flag excludes psychoacoustic metrics from analysis."""
        result = subprocess.run(
            [
                "uv", "run", "audioloop", "iterate",
                "--code", "-d", "1",
                "{ SinOsc.ar(440) * 0.3 ! 2 }",
                "--json", "--no-play", "--no-psychoacoustic"
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        assert result.returncode == 0

        data = json.loads(result.stdout)
        assert data["success"] is True
        # Psychoacoustic should be empty dict when skipped
        assert data["analysis"]["psychoacoustic"] == {}

    def test_keep_preserves_output_file(self, tmp_path):
        """--keep flag preserves the output WAV file."""
        output_file = tmp_path / "test_output.wav"

        result = subprocess.run(
            [
                "uv", "run", "audioloop", "iterate",
                "--code", "-d", "1",
                "{ SinOsc.ar(440) * 0.3 ! 2 }",
                "--json", "--no-play",
                "--output", str(output_file)
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        assert result.returncode == 0

        data = json.loads(result.stdout)
        assert data["success"] is True
        assert data["output_path"] == str(output_file)
        assert output_file.exists()

    def test_output_specifies_path(self, tmp_path):
        """--output flag specifies output path."""
        output_file = tmp_path / "custom_output.wav"

        result = subprocess.run(
            [
                "uv", "run", "audioloop", "iterate",
                "--code", "-d", "1",
                "{ SinOsc.ar(440) * 0.3 ! 2 }",
                "--json", "--no-play",
                "-o", str(output_file)
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        assert result.returncode == 0

        data = json.loads(result.stdout)
        assert data["output_path"] == str(output_file)
        assert output_file.exists()


class TestIterateOutputValidation:
    """Tests for JSON output structure validation."""

    def test_json_structure_complete(self):
        """JSON output has all expected top-level fields."""
        result = subprocess.run(
            [
                "uv", "run", "audioloop", "iterate",
                "--code", "-d", "1",
                "{ SinOsc.ar(440) * 0.3 ! 2 }",
                "--json", "--no-play"
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        data = json.loads(result.stdout)

        # Check all expected top-level keys
        assert "success" in data
        assert "render" in data
        assert "analysis" in data
        assert "played" in data
        assert "output_path" in data
        assert "total_time_sec" in data

    def test_render_section_complete(self):
        """Render section has expected fields."""
        result = subprocess.run(
            [
                "uv", "run", "audioloop", "iterate",
                "--code", "-d", "1",
                "{ SinOsc.ar(440) * 0.3 ! 2 }",
                "--json", "--no-play"
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        data = json.loads(result.stdout)
        render = data["render"]

        assert "success" in render
        assert "output_path" in render
        assert "duration_sec" in render
        assert "render_time_sec" in render
        assert "mode" in render

    def test_analysis_section_complete(self):
        """Analysis section has expected structure when successful."""
        result = subprocess.run(
            [
                "uv", "run", "audioloop", "iterate",
                "--code", "-d", "1",
                "{ SinOsc.ar(440) * 0.3 ! 2 }",
                "--json", "--no-play"
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        data = json.loads(result.stdout)
        analysis = data["analysis"]

        assert "file" in analysis
        assert "duration_sec" in analysis
        assert "sample_rate" in analysis
        assert "channels" in analysis
        assert "spectral" in analysis
        assert "temporal" in analysis
        assert "stereo" in analysis
        assert "loudness_lufs" in analysis

    def test_total_time_is_numeric(self):
        """total_time_sec is a valid number."""
        result = subprocess.run(
            [
                "uv", "run", "audioloop", "iterate",
                "--code", "-d", "1",
                "{ SinOsc.ar(440) * 0.3 ! 2 }",
                "--json", "--no-play"
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        data = json.loads(result.stdout)
        assert isinstance(data["total_time_sec"], (int, float))
        assert data["total_time_sec"] > 0


class TestIterateExitCodes:
    """Tests for exit code correctness."""

    def test_success_exit_code_zero(self):
        """Successful iterate returns exit code 0."""
        result = subprocess.run(
            [
                "uv", "run", "audioloop", "iterate",
                "--code", "-d", "1",
                "{ SinOsc.ar(440) * 0.3 ! 2 }",
                "--json", "--no-play"
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        assert result.returncode == 0

    def test_file_not_found_exit_code_two(self):
        """File not found returns exit code 2 (system error)."""
        result = subprocess.run(
            [
                "uv", "run", "audioloop", "iterate",
                "nonexistent.scd",
                "-d", "1",
                "--json", "--no-play"
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 2

    def test_missing_duration_exit_code_two(self):
        """Missing required duration returns exit code 2 (system error)."""
        result = subprocess.run(
            [
                "uv", "run", "audioloop", "iterate",
                "--code",
                "{ SinOsc.ar(440) }",
                "--json", "--no-play"
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 2
