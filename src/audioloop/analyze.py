"""Audio analysis module for feature extraction.

Extracts spectral, temporal, and stereo features from WAV files
using librosa and pyloudnorm.
"""

from dataclasses import dataclass, field
from pathlib import Path

import librosa
import numpy as np
import pyloudnorm as pyln
import soundfile as sf


class AnalysisError(Exception):
    """Raised when audio analysis fails."""

    pass


@dataclass
class SpectralFeatures:
    """Spectral features for a single channel."""

    centroid_hz: float
    rolloff_hz: float
    flatness: float
    bandwidth_hz: float


@dataclass
class TemporalFeatures:
    """Temporal/dynamics features."""

    attack_ms: float
    rms: float
    crest_factor: float


@dataclass
class StereoFeatures:
    """Stereo imaging features."""

    width: float
    correlation: float


@dataclass
class AnalysisResult:
    """Complete analysis result for an audio file."""

    file: str
    duration_sec: float
    sample_rate: int
    channels: int
    spectral: dict = field(default_factory=dict)  # left/right sub-dicts
    temporal: dict = field(default_factory=dict)
    stereo: dict = field(default_factory=dict)
    loudness_lufs: float = 0.0

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "file": self.file,
            "duration_sec": self.duration_sec,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "spectral": self.spectral,
            "temporal": self.temporal,
            "stereo": self.stereo,
            "loudness_lufs": self.loudness_lufs,
        }


def _compute_spectral_features(y: np.ndarray, sr: int) -> SpectralFeatures:
    """Compute spectral features for a single channel.

    Args:
        y: Audio signal (1D array).
        sr: Sample rate.

    Returns:
        SpectralFeatures with mean values over all frames.
    """
    # Add small constant to avoid issues with silence
    y_safe = y + 1e-10

    # Spectral centroid (Hz) - mean over frames
    centroid = librosa.feature.spectral_centroid(y=y_safe, sr=sr)
    centroid_mean = float(np.mean(centroid))

    # Spectral rolloff (Hz) - frequency below which 85% of energy
    rolloff = librosa.feature.spectral_rolloff(y=y_safe, sr=sr, roll_percent=0.85)
    rolloff_mean = float(np.mean(rolloff))

    # Spectral flatness (0-1, higher = more noise-like)
    flatness = librosa.feature.spectral_flatness(y=y_safe)
    flatness_mean = float(np.mean(flatness))

    # Spectral bandwidth (Hz)
    bandwidth = librosa.feature.spectral_bandwidth(y=y_safe, sr=sr)
    bandwidth_mean = float(np.mean(bandwidth))

    return SpectralFeatures(
        centroid_hz=centroid_mean,
        rolloff_hz=rolloff_mean,
        flatness=flatness_mean,
        bandwidth_hz=bandwidth_mean,
    )


def _compute_temporal_features(y: np.ndarray, sr: int) -> TemporalFeatures:
    """Compute temporal/dynamics features.

    Args:
        y: Audio signal (1D array, mono or combined).
        sr: Sample rate.

    Returns:
        TemporalFeatures with attack time, RMS, and crest factor.
    """
    # RMS energy (overall)
    rms_overall = float(np.sqrt(np.mean(y**2)))

    # Peak amplitude
    peak = float(np.max(np.abs(y)))

    # Crest factor (peak / RMS)
    crest_factor = peak / (rms_overall + 1e-10)

    # Attack time estimation (time to reach 90% of peak)
    envelope = np.abs(y)
    threshold = 0.9 * peak
    attack_indices = np.where(envelope >= threshold)[0]

    if len(attack_indices) > 0:
        attack_samples = attack_indices[0]
        attack_ms = float((attack_samples / sr) * 1000)
    else:
        attack_ms = 0.0

    return TemporalFeatures(
        attack_ms=attack_ms,
        rms=rms_overall,
        crest_factor=crest_factor,
    )


def _compute_stereo_features(left: np.ndarray, right: np.ndarray) -> StereoFeatures:
    """Compute stereo imaging features.

    Args:
        left: Left channel signal.
        right: Right channel signal.

    Returns:
        StereoFeatures with width and correlation.
    """
    # Mid/Side encoding
    mid = (left + right) / 2
    side = (left - right) / 2

    # Stereo width (side energy / total energy)
    mid_energy = np.sum(mid**2)
    side_energy = np.sum(side**2)
    width = float(side_energy / (mid_energy + side_energy + 1e-10))

    # L-R correlation (-1 to +1)
    # +1 = identical, 0 = uncorrelated, -1 = out of phase
    if np.std(left) > 1e-10 and np.std(right) > 1e-10:
        correlation = float(np.corrcoef(left, right)[0, 1])
    else:
        correlation = 1.0  # Identical (silent or constant)

    return StereoFeatures(width=width, correlation=correlation)


def _compute_loudness_lufs(y: np.ndarray, sr: int) -> float:
    """Compute integrated loudness in LUFS.

    Args:
        y: Audio signal (can be mono or stereo, shape: samples or 2xsamples).
        sr: Sample rate.

    Returns:
        Integrated loudness in dB LUFS.
    """
    # pyloudnorm expects (samples, channels) for stereo
    if y.ndim == 1:
        audio = y
    else:
        # librosa uses (channels, samples), pyloudnorm wants (samples, channels)
        audio = y.T

    meter = pyln.Meter(sr)
    loudness = meter.integrated_loudness(audio)
    return float(loudness)


def analyze(path: Path) -> AnalysisResult:
    """Analyze an audio file and extract features.

    Args:
        path: Path to WAV file.

    Returns:
        AnalysisResult with all extracted features.

    Raises:
        AnalysisError: If file cannot be read or analyzed.
    """
    path = Path(path)

    if not path.exists():
        raise AnalysisError(f"File not found: {path}")

    try:
        # Load audio at native sample rate
        y, sr = librosa.load(str(path), sr=None, mono=False)
    except Exception as e:
        raise AnalysisError(f"Failed to load audio file: {e}") from e

    # Get basic info
    duration = float(librosa.get_duration(y=y, sr=sr))

    # Handle mono vs stereo
    if y.ndim == 1:
        # Mono: duplicate to left/right
        channels = 1
        left = y
        right = y
    else:
        channels = y.shape[0]
        if channels >= 2:
            left = y[0]
            right = y[1]
        else:
            left = y[0]
            right = y[0]

    # Compute spectral features for each channel
    left_spectral = _compute_spectral_features(left, sr)
    right_spectral = _compute_spectral_features(right, sr)

    spectral = {
        "left": {
            "centroid_hz": left_spectral.centroid_hz,
            "rolloff_hz": left_spectral.rolloff_hz,
            "flatness": left_spectral.flatness,
            "bandwidth_hz": left_spectral.bandwidth_hz,
        },
        "right": {
            "centroid_hz": right_spectral.centroid_hz,
            "rolloff_hz": right_spectral.rolloff_hz,
            "flatness": right_spectral.flatness,
            "bandwidth_hz": right_spectral.bandwidth_hz,
        },
    }

    # Compute temporal features on combined signal
    combined = (left + right) / 2
    temporal_features = _compute_temporal_features(combined, sr)
    temporal = {
        "attack_ms": temporal_features.attack_ms,
        "rms": temporal_features.rms,
        "crest_factor": temporal_features.crest_factor,
    }

    # Compute stereo features
    stereo_features = _compute_stereo_features(left, right)
    stereo = {
        "width": stereo_features.width,
        "correlation": stereo_features.correlation,
    }

    # Compute loudness
    # For LUFS, pass the original signal
    if y.ndim == 1:
        loudness_lufs = _compute_loudness_lufs(y, sr)
    else:
        loudness_lufs = _compute_loudness_lufs(y, sr)

    return AnalysisResult(
        file=str(path),
        duration_sec=duration,
        sample_rate=sr,
        channels=channels,
        spectral=spectral,
        temporal=temporal,
        stereo=stereo,
        loudness_lufs=loudness_lufs,
    )
