"""Tests for the compare command."""

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from audioloop.analyze import AnalysisResult
from audioloop.compare import (
    ComparisonResult,
    FeatureDelta,
    compare_audio,
    format_comparison_human,
)


# Use the test fixture
FIXTURE_PATH = Path(__file__).parent / "fixtures" / "test_tone.wav"


class TestCompareAudioFunction:
    """Tests for the compare_audio function."""

    def test_compare_identical_files(self):
        """Same file should have all deltas unchanged (zero)."""
        result = compare_audio(FIXTURE_PATH, FIXTURE_PATH)

        assert result.file_a == str(FIXTURE_PATH)
        assert result.file_b == str(FIXTURE_PATH)
        assert result.duration_a == result.duration_b

        # All deltas should be unchanged
        for key, delta in result.deltas.items():
            assert delta.direction == "unchanged", f"{key} should be unchanged"
            assert delta.delta == 0.0 or abs(delta.delta) < 1e-10, (
                f"{key} delta should be zero"
            )
            assert not delta.significant, f"{key} should not be significant"

    def test_direction_and_significance(self):
        """Test that direction and significance are computed correctly."""
        # Mock analyze to return controlled values
        mock_result_a = MagicMock(spec=AnalysisResult)
        mock_result_a.duration_sec = 1.0
        mock_result_a.to_dict.return_value = {
            "spectral": {
                "left": {"centroid_hz": 1000.0, "rolloff_hz": 2000.0}
            },
            "temporal": {"attack_ms": 50.0, "rms": 0.5},
        }

        mock_result_b = MagicMock(spec=AnalysisResult)
        mock_result_b.duration_sec = 1.0
        mock_result_b.to_dict.return_value = {
            "spectral": {
                "left": {"centroid_hz": 800.0, "rolloff_hz": 2400.0}  # down 20%, up 20%
            },
            "temporal": {"attack_ms": 52.0, "rms": 0.5},  # up 4%, unchanged
        }

        with patch("audioloop.compare.analyze") as mock_analyze:
            mock_analyze.side_effect = [mock_result_a, mock_result_b]

            result = compare_audio(Path("a.wav"), Path("b.wav"))

        # Check centroid went down significantly
        centroid_delta = result.deltas["spectral.left.centroid_hz"]
        assert centroid_delta.direction == "down"
        assert centroid_delta.significant
        assert centroid_delta.interpretation == "darker/warmer"

        # Check rolloff went up 20% (should be significant)
        rolloff_delta = result.deltas["spectral.left.rolloff_hz"]
        assert rolloff_delta.direction == "up"
        assert rolloff_delta.significant
        assert rolloff_delta.interpretation == "more high frequency content"

        # Check attack went up but not significantly (4% < 10%)
        attack_delta = result.deltas["temporal.attack_ms"]
        assert attack_delta.direction == "up"
        assert not attack_delta.significant

        # Check rms unchanged
        rms_delta = result.deltas["temporal.rms"]
        assert rms_delta.direction == "unchanged"
        assert not rms_delta.significant

    def test_to_dict_serialization(self):
        """Test that ComparisonResult.to_dict() produces valid JSON."""
        result = compare_audio(FIXTURE_PATH, FIXTURE_PATH)
        data = result.to_dict()

        # Should be JSON serializable
        json_str = json.dumps(data)
        parsed = json.loads(json_str)

        assert parsed["file_a"] == str(FIXTURE_PATH)
        assert parsed["file_b"] == str(FIXTURE_PATH)
        assert "deltas" in parsed
        assert "summary" in parsed


class TestCompareFormatting:
    """Tests for comparison output formatting."""

    def test_format_comparison_human_output(self):
        """Verify human-readable format includes key elements."""
        result = compare_audio(FIXTURE_PATH, FIXTURE_PATH)
        output = format_comparison_human(result)

        # Should contain comparison header
        assert "Comparison:" in output
        # Rich adds ANSI codes to paths, so check for filename
        assert "test_tone.wav" in output

        # Should contain category headers
        assert "SPECTRAL" in output
        assert "TEMPORAL" in output
        assert "STEREO" in output
        assert "LOUDNESS" in output

        # Should indicate no significant changes for identical files
        assert "no significant changes" in output.lower()


class TestCompareCLI:
    """CLI integration tests for the compare command."""

    def test_compare_cli_human_output(self):
        """Verify human-readable CLI output contains expected elements."""
        from typer.testing import CliRunner
        from audioloop.cli import app

        runner = CliRunner()
        result = runner.invoke(
            app, ["compare", str(FIXTURE_PATH), str(FIXTURE_PATH)]
        )

        assert result.exit_code == 0
        assert "Comparison:" in result.stdout
        assert "SPECTRAL" in result.stdout

    def test_compare_cli_json_output(self):
        """Verify JSON output is valid and contains expected structure."""
        from typer.testing import CliRunner
        from audioloop.cli import app

        runner = CliRunner()
        result = runner.invoke(
            app, ["compare", str(FIXTURE_PATH), str(FIXTURE_PATH), "--json"]
        )

        assert result.exit_code == 0

        # Parse JSON
        data = json.loads(result.stdout)

        assert data["file_a"] == str(FIXTURE_PATH)
        assert data["file_b"] == str(FIXTURE_PATH)
        assert "deltas" in data
        assert "summary" in data

        # Check delta structure
        deltas = data["deltas"]
        assert len(deltas) > 0

        # Check a specific delta has expected fields
        first_key = list(deltas.keys())[0]
        first_delta = deltas[first_key]
        assert "value_a" in first_delta
        assert "value_b" in first_delta
        assert "delta" in first_delta
        assert "direction" in first_delta
        assert "significant" in first_delta

    def test_compare_file_not_found(self):
        """Verify exit code 2 when file doesn't exist."""
        result = subprocess.run(
            ["uv", "run", "audioloop", "compare", "nonexistent.wav", str(FIXTURE_PATH)],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 2
        assert "not found" in result.stderr.lower() or "not found" in result.stdout.lower()

    def test_compare_second_file_not_found(self):
        """Verify exit code 2 when second file doesn't exist."""
        result = subprocess.run(
            ["uv", "run", "audioloop", "compare", str(FIXTURE_PATH), "nonexistent.wav"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 2
        assert "not found" in result.stderr.lower() or "not found" in result.stdout.lower()

    def test_compare_help(self):
        """Verify compare command appears in help output."""
        result = subprocess.run(
            ["uv", "run", "audioloop", "--help"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "compare" in result.stdout.lower()
