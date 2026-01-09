"""Tests for the audio analysis module."""

import numpy as np
import pytest
import soundfile as sf
from pathlib import Path

from audioloop.analyze import analyze, AnalysisResult, AnalysisError


@pytest.fixture
def fixtures_dir(tmp_path):
    """Return path to fixtures directory, creating test fixtures if needed."""
    return tmp_path


@pytest.fixture
def test_tone_stereo(fixtures_dir):
    """Generate a stereo 440Hz sine wave test fixture.

    Returns:
        Path to the generated WAV file.
    """
    sr = 44100
    duration = 1.0
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)

    # 440Hz sine wave
    freq = 440.0
    sine = 0.5 * np.sin(2 * np.pi * freq * t)

    # Stereo: identical L/R
    stereo = np.column_stack([sine, sine])

    path = fixtures_dir / "test_tone_stereo.wav"
    sf.write(path, stereo, sr)
    return path


@pytest.fixture
def test_tone_mono(fixtures_dir):
    """Generate a mono 440Hz sine wave test fixture."""
    sr = 44100
    duration = 1.0
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)

    freq = 440.0
    sine = 0.5 * np.sin(2 * np.pi * freq * t)

    path = fixtures_dir / "test_tone_mono.wav"
    sf.write(path, sine, sr)
    return path


@pytest.fixture
def test_stereo_wide(fixtures_dir):
    """Generate a stereo file with different L/R content (wide stereo)."""
    sr = 44100
    duration = 1.0
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)

    # Different frequencies for L/R
    left = 0.5 * np.sin(2 * np.pi * 440.0 * t)
    right = 0.5 * np.sin(2 * np.pi * 880.0 * t)

    stereo = np.column_stack([left, right])

    path = fixtures_dir / "test_stereo_wide.wav"
    sf.write(path, stereo, sr)
    return path


class TestAnalyzeBasics:
    """Basic analysis tests."""

    def test_analyze_returns_result(self, test_tone_stereo):
        """Basic analysis returns AnalysisResult with all fields."""
        result = analyze(test_tone_stereo)

        assert isinstance(result, AnalysisResult)
        assert result.file == str(test_tone_stereo)
        assert result.sample_rate == 44100
        assert result.channels == 2

        # Check spectral has left/right
        assert "left" in result.spectral
        assert "right" in result.spectral
        assert "centroid_hz" in result.spectral["left"]
        assert "rolloff_hz" in result.spectral["left"]
        assert "flatness" in result.spectral["left"]
        assert "bandwidth_hz" in result.spectral["left"]

        # Check temporal
        assert "attack_ms" in result.temporal
        assert "rms" in result.temporal
        assert "crest_factor" in result.temporal

        # Check stereo
        assert "width" in result.stereo
        assert "correlation" in result.stereo

        # Check loudness
        assert result.loudness_lufs < 0  # Should be negative dB LUFS

    def test_duration_correct(self, test_tone_stereo):
        """Duration matches expected (within tolerance)."""
        result = analyze(test_tone_stereo)

        # 1-second file
        assert abs(result.duration_sec - 1.0) < 0.1


class TestSpectralFeatures:
    """Tests for spectral feature extraction."""

    def test_spectral_features_reasonable(self, test_tone_stereo):
        """Centroid for 440Hz tone should be near 440Hz."""
        result = analyze(test_tone_stereo)

        # Pure sine wave centroid should be at the fundamental
        # Allow 50Hz tolerance for windowing effects
        left_centroid = result.spectral["left"]["centroid_hz"]
        right_centroid = result.spectral["right"]["centroid_hz"]

        assert abs(left_centroid - 440) < 50
        assert abs(right_centroid - 440) < 50

    def test_flatness_low_for_sine(self, test_tone_stereo):
        """Spectral flatness should be low for pure sine (tonal)."""
        result = analyze(test_tone_stereo)

        # Sine wave is very tonal, flatness should be low (< 0.1)
        left_flatness = result.spectral["left"]["flatness"]
        assert left_flatness < 0.1


class TestTemporalFeatures:
    """Tests for temporal/dynamics features."""

    def test_rms_nonzero(self, test_tone_stereo):
        """RMS should be positive for non-silent audio."""
        result = analyze(test_tone_stereo)

        assert result.temporal["rms"] > 0

    def test_crest_factor_reasonable(self, test_tone_stereo):
        """Crest factor for sine wave should be near sqrt(2) = 1.414."""
        result = analyze(test_tone_stereo)

        # Sine wave crest factor is sqrt(2) ≈ 1.414
        crest = result.temporal["crest_factor"]
        assert 1.3 < crest < 1.6


class TestStereoFeatures:
    """Tests for stereo imaging features."""

    def test_identical_lr_narrow_width(self, test_tone_stereo):
        """Width should be near 0 for identical L/R content."""
        result = analyze(test_tone_stereo)

        # Identical L/R = mono = no side energy = width near 0
        assert result.stereo["width"] < 0.01

    def test_identical_lr_high_correlation(self, test_tone_stereo):
        """Correlation should be near 1.0 for identical L/R."""
        result = analyze(test_tone_stereo)

        assert result.stereo["correlation"] > 0.99

    def test_different_lr_wider(self, test_stereo_wide):
        """Width should be higher for different L/R content."""
        result = analyze(test_stereo_wide)

        # Different L/R should have significant side energy
        assert result.stereo["width"] > 0.3

    def test_different_lr_lower_correlation(self, test_stereo_wide):
        """Correlation should be lower for uncorrelated L/R."""
        result = analyze(test_stereo_wide)

        # Different frequencies will have lower correlation
        assert result.stereo["correlation"] < 0.5


class TestMonoHandling:
    """Tests for mono file handling."""

    def test_mono_handling(self, test_tone_mono):
        """Mono files should have left == right spectral features."""
        result = analyze(test_tone_mono)

        assert result.channels == 1

        # Spectral features should be identical for L/R
        assert result.spectral["left"]["centroid_hz"] == result.spectral["right"]["centroid_hz"]
        assert result.spectral["left"]["rolloff_hz"] == result.spectral["right"]["rolloff_hz"]
        assert result.spectral["left"]["flatness"] == result.spectral["right"]["flatness"]


class TestErrorHandling:
    """Tests for error handling."""

    def test_invalid_file_raises(self, fixtures_dir):
        """Non-existent file raises AnalysisError."""
        nonexistent = fixtures_dir / "nonexistent.wav"

        with pytest.raises(AnalysisError) as exc_info:
            analyze(nonexistent)

        assert "not found" in str(exc_info.value).lower()

    def test_invalid_format_raises(self, fixtures_dir):
        """Non-audio file raises AnalysisError."""
        # Create a text file with .wav extension
        fake_wav = fixtures_dir / "fake.wav"
        fake_wav.write_text("not audio data")

        with pytest.raises(AnalysisError):
            analyze(fake_wav)


class TestToDict:
    """Tests for serialization."""

    def test_to_dict_returns_dict(self, test_tone_stereo):
        """to_dict() returns a serializable dictionary."""
        result = analyze(test_tone_stereo)
        d = result.to_dict()

        assert isinstance(d, dict)
        assert d["file"] == str(test_tone_stereo)
        assert "spectral" in d
        assert "temporal" in d
        assert "stereo" in d
        assert "loudness_lufs" in d
        assert "psychoacoustic" in d


class TestPsychoacoustic:
    """Tests for psychoacoustic feature integration."""

    def test_psychoacoustic_field_exists(self, test_tone_stereo):
        """AnalysisResult includes psychoacoustic field."""
        result = analyze(test_tone_stereo)

        # Field should exist as dict (may be empty if MoSQITo not installed)
        assert isinstance(result.psychoacoustic, dict)

    def test_psychoacoustic_in_to_dict(self, test_tone_stereo):
        """to_dict() includes psychoacoustic in output."""
        result = analyze(test_tone_stereo)
        d = result.to_dict()

        assert "psychoacoustic" in d
        assert isinstance(d["psychoacoustic"], dict)

    def test_psychoacoustic_has_expected_keys_if_available(self, test_tone_stereo):
        """If MoSQITo installed, psychoacoustic has expected keys."""
        result = analyze(test_tone_stereo)

        # Skip test if MoSQITo not installed
        if not result.psychoacoustic:
            pytest.skip("MoSQITo not installed - skipping key validation")

        expected_keys = ["loudness_sone", "loudness_sone_max", "sharpness_acum", "roughness_asper"]
        for key in expected_keys:
            assert key in result.psychoacoustic, f"Missing key: {key}"
            assert isinstance(result.psychoacoustic[key], float), f"{key} should be float"

    def test_psychoacoustic_values_reasonable(self, test_tone_stereo):
        """If MoSQITo installed, psychoacoustic values are in reasonable ranges."""
        result = analyze(test_tone_stereo)

        # Skip test if MoSQITo not installed
        if not result.psychoacoustic:
            pytest.skip("MoSQITo not installed - skipping value validation")

        # Loudness in sones should be positive
        assert result.psychoacoustic["loudness_sone"] >= 0
        assert result.psychoacoustic["loudness_sone_max"] >= result.psychoacoustic["loudness_sone"]

        # Sharpness in acum should be positive
        assert result.psychoacoustic["sharpness_acum"] >= 0

        # Roughness in asper should be non-negative
        assert result.psychoacoustic["roughness_asper"] >= 0
