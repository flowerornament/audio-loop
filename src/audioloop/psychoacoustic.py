"""Psychoacoustic metrics via MoSQITo library.

Computes Zwicker loudness, sharpness, and roughness for perceptual audio analysis.
MoSQITo is an optional dependency - returns None if not installed.

Performance note: Metrics run serially (~1.1s for 1-second audio). Parallelization
was tested but ProcessPoolExecutor overhead (~500ms) exceeded the benefit since
loudness_zwtv (~900ms) dominates and cannot be parallelized internally.
"""

import logging

import numpy as np

logger = logging.getLogger(__name__)


def prepare_for_mosqito(y: np.ndarray, sr: int) -> tuple[np.ndarray, int]:
    """Convert audio to MoSQITo-compatible format (48kHz mono float32).

    MoSQITo requires 48kHz mono audio. This function handles resampling
    and channel conversion as needed.

    Args:
        y: Audio signal (mono or stereo). Shape: (samples,) or (channels, samples).
        sr: Original sample rate.

    Returns:
        Tuple of (resampled mono signal as float32, 48000).
    """
    import librosa

    # Convert stereo to mono by averaging channels
    if y.ndim > 1:
        y = np.mean(y, axis=0)

    # Resample to 48kHz if needed
    if sr != 48000:
        y = librosa.resample(y, orig_sr=sr, target_sr=48000)

    # Cast to float32 for MoSQITo
    y = y.astype(np.float32)

    return y, 48000


def compute_psychoacoustic(y: np.ndarray, sr: int) -> dict | None:
    """Compute psychoacoustic metrics using MoSQITo.

    Computes Zwicker loudness (sones), sharpness (acum), and roughness (asper)
    using the MoSQITo library. Returns None if MoSQITo is not installed.

    All metrics use relative values (calib=1.0) since we don't have
    calibrated SPL measurements.

    Args:
        y: Audio signal (mono or stereo).
        sr: Sample rate.

    Returns:
        Dictionary with psychoacoustic metrics, or None if MoSQITo unavailable.
        Keys: loudness_sone, loudness_sone_max, sharpness_acum, roughness_asper
    """
    # Lazy import - MoSQITo is optional
    try:
        from mosqito.sq_metrics import (
            loudness_zwtv,
            roughness_dw,
            sharpness_din_from_loudness,
        )
    except ImportError:
        logger.debug("MoSQITo not installed - skipping psychoacoustic metrics")
        return None

    try:
        # Preprocess to 48kHz mono
        y_48k, fs = prepare_for_mosqito(y, sr)

        # Check for very short or silent audio
        if len(y_48k) < 4800:  # Less than 0.1 seconds at 48kHz
            logger.warning("Audio too short for psychoacoustic analysis")
            return None

        if np.max(np.abs(y_48k)) < 1e-10:
            logger.warning("Audio is silent - skipping psychoacoustic analysis")
            return None

        # Compute Zwicker loudness (time-varying)
        # field_type="free" for free-field (headphone/near-field) listening
        N, N_spec, bark_axis, time_axis = loudness_zwtv(y_48k, fs=fs, field_type="free")

        # Compute sharpness from loudness (DIN 45692)
        # weighting="din" for DIN 45692 standard
        S = sharpness_din_from_loudness(N, N_spec, weighting="din")

        # Compute roughness (Daniel & Weber model)
        R, time_axis_r, _, _ = roughness_dw(y_48k, fs=fs)

        return {
            "loudness_sone": float(np.mean(N)),
            "loudness_sone_max": float(np.max(N)),
            "sharpness_acum": float(np.mean(S)),
            "roughness_asper": float(np.mean(R)),
        }

    except Exception as e:
        # MoSQITo can fail on edge cases (very short audio, unusual content)
        logger.warning(f"Psychoacoustic analysis failed: {e}")
        return None
