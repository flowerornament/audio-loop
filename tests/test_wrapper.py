"""Tests for the wrapper module."""

from pathlib import Path

from audioloop.wrapper import needs_wrapping, wrap_function, replace_placeholders


class TestNeedsWrapping:
    """Tests for the needs_wrapping function."""

    def test_needs_wrapping_simple_function(self):
        """Simple function returns True."""
        code = "{ SinOsc.ar(440) }"
        assert needs_wrapping(code) is True

    def test_needs_wrapping_complex_function(self):
        """Complex function without recordNRT returns True."""
        code = """
        {
            var sig = SinOsc.ar(440);
            LPF.ar(sig, 1000) * 0.5
        }
        """
        assert needs_wrapping(code) is True

    def test_needs_wrapping_full_nrt(self):
        """Full NRT code returns False."""
        code = """
        (
        var score = Score([]);
        score.recordNRT(
            outputFilePath: "__OUTPUT_PATH__",
            duration: 1.0
        );
        )
        """
        assert needs_wrapping(code) is False

    def test_needs_wrapping_recordnrt_in_comment(self):
        """recordNRT in a comment should still return False (conservative)."""
        # This is conservative behavior - if recordNRT appears anywhere,
        # we assume the user knows what they're doing.
        code = """
        // This uses recordNRT for rendering
        { SinOsc.ar(440) }
        """
        assert needs_wrapping(code) is False


class TestWrapFunction:
    """Tests for the wrap_function function."""

    def test_wrap_function_generates_valid_code(self):
        """Wrapped code contains NRT boilerplate."""
        code = "{ SinOsc.ar(440) }"
        output_path = Path("/tmp/output.wav")
        result = wrap_function(code, duration=2.0, output_path=output_path)

        # Should contain key NRT elements
        assert "recordNRT" in result
        assert "SynthDef" in result
        assert "Score" in result
        assert "0.exit" in result

    def test_wrap_function_includes_user_code(self):
        """User code is included in wrapped output."""
        code = "{ SinOsc.ar(440) * 0.3 ! 2 }"
        output_path = Path("/tmp/output.wav")
        result = wrap_function(code, duration=2.0, output_path=output_path)

        assert "SinOsc.ar(440) * 0.3 ! 2" in result

    def test_wrap_function_includes_duration(self):
        """Duration is included in wrapped output."""
        code = "{ SinOsc.ar(440) }"
        output_path = Path("/tmp/output.wav")
        result = wrap_function(code, duration=3.5, output_path=output_path)

        assert "3.5" in result

    def test_wrap_function_includes_output_path(self):
        """Output path is included in wrapped output."""
        code = "{ SinOsc.ar(440) }"
        output_path = Path("/tmp/my_output.wav")
        result = wrap_function(code, duration=2.0, output_path=output_path)

        assert "/tmp/my_output.wav" in result

    def test_wrap_function_strips_whitespace(self):
        """User code whitespace is stripped."""
        code = "  { SinOsc.ar(440) }  \n"
        output_path = Path("/tmp/output.wav")
        result = wrap_function(code, duration=2.0, output_path=output_path)

        # Code should be stripped
        assert "userFunc = { SinOsc.ar(440) }" in result


class TestReplacePlaceholders:
    """Tests for the replace_placeholders function."""

    def test_placeholder_replacement_output_path(self):
        """__OUTPUT_PATH__ is replaced correctly."""
        code = 'outputFilePath: "__OUTPUT_PATH__"'
        output_path = Path("/tmp/test.wav")
        result = replace_placeholders(code, output_path)

        assert result == 'outputFilePath: "/tmp/test.wav"'

    def test_placeholder_replacement_duration(self):
        """__DURATION__ is replaced when duration provided."""
        code = "var duration = __DURATION__;"
        output_path = Path("/tmp/test.wav")
        result = replace_placeholders(code, output_path, duration=4.5)

        assert result == "var duration = 4.5;"

    def test_placeholder_replacement_without_duration(self):
        """__DURATION__ is not replaced when duration not provided."""
        code = "var duration = __DURATION__;"
        output_path = Path("/tmp/test.wav")
        result = replace_placeholders(code, output_path)

        # Duration placeholder remains
        assert result == "var duration = __DURATION__;"

    def test_placeholder_replacement_multiple(self):
        """Multiple placeholders are replaced correctly."""
        code = '''
        var outputPath = "__OUTPUT_PATH__";
        var duration = __DURATION__;
        outputFilePath: "__OUTPUT_PATH__"
        '''
        output_path = Path("/tmp/test.wav")
        result = replace_placeholders(code, output_path, duration=2.0)

        assert "__OUTPUT_PATH__" not in result
        assert "__DURATION__" not in result
        assert '"/tmp/test.wav"' in result
        assert "2.0" in result
