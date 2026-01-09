"""Integration tests for the render module."""

import json
import tempfile
from pathlib import Path

import pytest

from audioloop.render import render, RenderResult
from audioloop.sc_paths import validate_sc_installation


# Check if SuperCollider is available
def sc_available() -> bool:
    """Check if SuperCollider is installed and available."""
    is_valid, _ = validate_sc_installation()
    return is_valid


# Skip marker for tests requiring SC
requires_sc = pytest.mark.skipif(
    not sc_available(),
    reason="SuperCollider not installed"
)


# Fixture paths
FIXTURES_DIR = Path(__file__).parent / "fixtures"
FULL_NRT_FIXTURE = FIXTURES_DIR / "full_nrt.scd"
SIMPLE_FUNCTION_FIXTURE = FIXTURES_DIR / "simple_function.scd"
SYNTAX_ERROR_FIXTURE = FIXTURES_DIR / "syntax_error.scd"
RUNTIME_ERROR_FIXTURE = FIXTURES_DIR / "runtime_error.scd"


@pytest.fixture
def temp_wav_path():
    """Provide a temporary WAV file path and clean up after test."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        path = Path(f.name)
    yield path
    # Cleanup
    if path.exists():
        path.unlink()


class TestRenderFullNRT:
    """Tests for full NRT mode rendering."""

    @requires_sc
    def test_render_full_nrt(self, temp_wav_path: Path):
        """Renders full_nrt.scd and verifies WAV output."""
        result = render(
            input_path=FULL_NRT_FIXTURE,
            output_path=temp_wav_path,
            timeout=60.0,
        )

        assert result.success is True
        assert result.mode == "full_nrt"
        # Use resolve() to handle macOS /var -> /private/var symlink
        assert result.output_path == temp_wav_path.resolve()
        assert result.output_path.exists()
        assert result.output_path.stat().st_size > 0
        assert result.duration_sec is not None
        assert result.duration_sec > 0.9  # Should be ~1 second
        assert result.error is None

    @requires_sc
    def test_render_full_nrt_custom_output_path(self, temp_wav_path: Path):
        """Verifies custom output path works."""
        custom_path = temp_wav_path.parent / "custom_output.wav"
        try:
            result = render(
                input_path=FULL_NRT_FIXTURE,
                output_path=custom_path,
                timeout=60.0,
            )

            assert result.success is True
            # Use resolve() to handle macOS /var -> /private/var symlink
            assert result.output_path == custom_path.resolve()
            assert custom_path.exists()
        finally:
            if custom_path.exists():
                custom_path.unlink()


class TestRenderWrapped:
    """Tests for wrapped function mode rendering."""

    @requires_sc
    def test_render_wrapped_function(self, temp_wav_path: Path):
        """Renders simple_function.scd with --duration and verifies WAV."""
        result = render(
            input_path=SIMPLE_FUNCTION_FIXTURE,
            output_path=temp_wav_path,
            timeout=60.0,
            duration=2.0,
        )

        assert result.success is True
        assert result.mode == "wrapped"
        # Use resolve() to handle macOS /var -> /private/var symlink
        assert result.output_path == temp_wav_path.resolve()
        assert result.output_path.exists()
        assert result.output_path.stat().st_size > 0
        assert result.duration_sec is not None
        assert result.duration_sec > 1.9  # Should be ~2 seconds
        assert result.error is None

    def test_render_wrapped_without_duration(self, temp_wav_path: Path):
        """Verifies error when --duration missing for simple function."""
        result = render(
            input_path=SIMPLE_FUNCTION_FIXTURE,
            output_path=temp_wav_path,
            timeout=60.0,
            # No duration specified
        )

        assert result.success is False
        assert result.mode == "wrapped"
        assert result.error is not None
        assert "duration" in result.error.message.lower()
        assert "--duration" in result.error.message


class TestRenderErrors:
    """Tests for error handling."""

    @requires_sc
    def test_render_syntax_error(self, temp_wav_path: Path):
        """Verifies error detection for syntax errors."""
        result = render(
            input_path=SYNTAX_ERROR_FIXTURE,
            output_path=temp_wav_path,
            timeout=20.0,  # Shorter timeout - syntax errors cause hang
        )

        assert result.success is False
        assert result.mode == "full_nrt"
        assert result.error is not None
        # Should contain syntax-related error message
        assert "syntax" in result.error.message.lower() or "unexpected" in result.error.message.lower()

    @requires_sc
    def test_render_runtime_error(self, temp_wav_path: Path):
        """Verifies error detection for runtime errors."""
        result = render(
            input_path=RUNTIME_ERROR_FIXTURE,
            output_path=temp_wav_path,
            timeout=20.0,
        )

        assert result.success is False
        assert result.error is not None
        # Should mention the undefined variable
        assert "unknownVariable" in result.error.message or "not defined" in result.error.message.lower()

    def test_render_missing_file(self, temp_wav_path: Path):
        """Verifies clean error for nonexistent input file."""
        nonexistent = Path("/nonexistent/path/file.scd")
        result = render(
            input_path=nonexistent,
            output_path=temp_wav_path,
            timeout=60.0,
        )

        assert result.success is False
        assert result.mode == "unknown"
        assert result.error is not None
        assert "not found" in result.error.message.lower()

    @requires_sc
    def test_render_timeout(self, temp_wav_path: Path):
        """Verifies timeout handling with a script that would hang."""
        # Syntax error causes sclang to hang in SC 3.14.x
        # Using a very short timeout to test timeout behavior
        result = render(
            input_path=SYNTAX_ERROR_FIXTURE,
            output_path=temp_wav_path,
            timeout=5.0,  # Very short timeout
        )

        assert result.success is False
        assert result.error is not None
        # Should either timeout or detect the error
        assert "timeout" in result.error.message.lower() or "syntax" in result.error.message.lower()


class TestRenderResult:
    """Tests for RenderResult structure."""

    @requires_sc
    def test_render_result_structure(self, temp_wav_path: Path):
        """Verifies RenderResult has all expected fields."""
        result = render(
            input_path=FULL_NRT_FIXTURE,
            output_path=temp_wav_path,
            timeout=60.0,
        )

        # Check all fields exist
        assert hasattr(result, "success")
        assert hasattr(result, "output_path")
        assert hasattr(result, "duration_sec")
        assert hasattr(result, "render_time_sec")
        assert hasattr(result, "error")
        assert hasattr(result, "sclang_output")
        assert hasattr(result, "mode")

        # Check types
        assert isinstance(result.success, bool)
        assert isinstance(result.render_time_sec, float)
        assert isinstance(result.mode, str)

    @requires_sc
    def test_json_output_format(self, temp_wav_path: Path):
        """Verifies JSON output matches expected schema."""
        result = render(
            input_path=FULL_NRT_FIXTURE,
            output_path=temp_wav_path,
            timeout=60.0,
        )

        # Build JSON output as CLI would
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

        # Should be valid JSON
        json_str = json.dumps(output_data)
        parsed = json.loads(json_str)

        assert parsed["success"] is True
        assert parsed["mode"] == "full_nrt"
        assert "output_path" in parsed
        assert "duration_sec" in parsed
        assert "render_time_sec" in parsed

    def test_json_output_format_error(self, temp_wav_path: Path):
        """Verifies JSON output with error matches expected schema."""
        result = render(
            input_path=SIMPLE_FUNCTION_FIXTURE,
            output_path=temp_wav_path,
            # Missing duration - will fail
        )

        # Build JSON output as CLI would
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

        # Should be valid JSON
        json_str = json.dumps(output_data)
        parsed = json.loads(json_str)

        assert parsed["success"] is False
        assert "error" in parsed
        assert "message" in parsed["error"]
