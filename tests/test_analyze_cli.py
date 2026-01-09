"""CLI integration tests for the analyze command."""

import json
import subprocess
from pathlib import Path

import pytest


# Use the test fixture created for CLI tests
FIXTURE_PATH = Path(__file__).parent / "fixtures" / "test_tone.wav"


class TestAnalyzeJsonOutput:
    """Tests for JSON output mode."""

    def test_analyze_json_output(self):
        """Run audioloop analyze with --json, verify valid JSON with expected keys."""
        result = subprocess.run(
            ["uv", "run", "audioloop", "analyze", str(FIXTURE_PATH), "--json"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Command failed: {result.stderr}"

        # Should be valid JSON
        data = json.loads(result.stdout)

        # Check all expected top-level keys
        assert "file" in data
        assert "duration_sec" in data
        assert "sample_rate" in data
        assert "channels" in data
        assert "spectral" in data
        assert "temporal" in data
        assert "stereo" in data
        assert "loudness_lufs" in data

    def test_analyze_json_schema(self):
        """Verify JSON output matches PROJECT.md schema structure."""
        result = subprocess.run(
            ["uv", "run", "audioloop", "analyze", str(FIXTURE_PATH), "--json"],
            capture_output=True,
            text=True,
        )

        data = json.loads(result.stdout)

        # Spectral has left/right
        assert "left" in data["spectral"]
        assert "right" in data["spectral"]

        # Spectral features per channel
        for channel in ["left", "right"]:
            assert "centroid_hz" in data["spectral"][channel]
            assert "rolloff_hz" in data["spectral"][channel]
            assert "flatness" in data["spectral"][channel]
            assert "bandwidth_hz" in data["spectral"][channel]

        # Temporal features
        assert "attack_ms" in data["temporal"]
        assert "rms" in data["temporal"]
        assert "crest_factor" in data["temporal"]

        # Stereo features
        assert "width" in data["stereo"]
        assert "correlation" in data["stereo"]

        # Values are numeric
        assert isinstance(data["loudness_lufs"], float)
        assert isinstance(data["duration_sec"], float)
        assert isinstance(data["sample_rate"], int)


class TestAnalyzeHumanOutput:
    """Tests for human-readable output mode."""

    def test_analyze_human_output(self):
        """Run audioloop analyze without --json, verify output contains expected sections."""
        result = subprocess.run(
            ["uv", "run", "audioloop", "analyze", str(FIXTURE_PATH)],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Command failed: {result.stderr}"

        # Output should contain expected sections
        output = result.stdout

        # Check for section headers (may have ANSI codes)
        assert "FILE INFO" in output
        assert "SPECTRAL" in output
        assert "DYNAMICS" in output
        assert "STEREO" in output
        assert "LOUDNESS" in output

        # Check for some expected values
        assert "Hz" in output  # Centroid, sample rate, rolloff
        assert "LUFS" in output  # Loudness


class TestAnalyzeErrorHandling:
    """Tests for error handling."""

    def test_analyze_file_not_found(self):
        """Run with nonexistent file, verify exit code 2."""
        result = subprocess.run(
            ["uv", "run", "audioloop", "analyze", "nonexistent_file.wav"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 2
        assert "not found" in result.stderr.lower() or "not found" in result.stdout.lower()

    def test_analyze_directory_not_file(self, tmp_path):
        """Run with a directory instead of file, verify exit code 2."""
        result = subprocess.run(
            ["uv", "run", "audioloop", "analyze", str(tmp_path)],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 2


class TestAnalyzeValues:
    """Tests for analysis value correctness."""

    def test_analyze_values_reasonable(self):
        """Verify analysis values are in reasonable ranges for test tone."""
        result = subprocess.run(
            ["uv", "run", "audioloop", "analyze", str(FIXTURE_PATH), "--json"],
            capture_output=True,
            text=True,
        )

        data = json.loads(result.stdout)

        # 440Hz sine wave should have centroid near 440-460 Hz
        centroid = data["spectral"]["left"]["centroid_hz"]
        assert 400 < centroid < 500, f"Centroid {centroid} out of expected range"

        # Sine wave crest factor should be near sqrt(2) = 1.414
        crest = data["temporal"]["crest_factor"]
        assert 1.3 < crest < 1.6, f"Crest factor {crest} out of expected range"

        # Identical L/R should have near-zero width
        width = data["stereo"]["width"]
        assert width < 0.01, f"Width {width} should be near zero for identical L/R"

        # Should be 1.0 second duration
        assert abs(data["duration_sec"] - 1.0) < 0.1
