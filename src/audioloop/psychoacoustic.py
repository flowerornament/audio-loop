"""Psychoacoustic metrics via MoSQITo library.

Computes Zwicker loudness, sharpness, and roughness for perceptual audio analysis.
MoSQITo is an optional dependency - returns None if not installed.

Performance note: Loudness (~900ms) and roughness (~200ms) are computed in parallel
using ProcessPoolExecutor. Sharpness (<1ms) runs after loudness since it depends
on the loudness output (N, N_spec).
"""

import logging
from concurrent.futures import ProcessPoolExecutor

import numpy as np

logger = logging.getLogger(__name__)


def _compute_loudness(y_48k: np.ndarray, fs: int) -> dict:
    """Compute Zwicker loudness in subprocess.

    Imports MoSQITo inside function for subprocess pickling.

    Args:
        y_48k: Audio signal at 48kHz mono.
        fs: Sample rate (48000).

    Returns:
        Dict with loudness_sone, loudness_sone_max, N, N_spec.
    """
    from mosqito.sq_metrics import loudness_zwtv

    N, N_spec, bark_axis, time_axis = loudness_zwtv(y_48k, fs=fs, field_type="free")

    return {
        "loudness_sone": float(np.mean(N)),
        "loudness_sone_max": float(np.max(N)),
        "N": N,  # Needed for sharpness computation
        "N_spec": N_spec,  # Needed for sharpness computation
    }


def _compute_roughness(y_48k: np.ndarray, fs: int) -> dict:
    """Compute roughness in subprocess.

    Imports MoSQITo inside function for subprocess pickling.

    Args:
        y_48k: Audio signal at 48kHz mono.
        fs: Sample rate (48000).

    Returns:
        Dict with roughness_asper.
    """
    from mosqito.sq_metrics import roughness_dw

    R, time_axis_r, _, _ = roughness_dw(y_48k, fs=fs)

    return {"roughness_asper": float(np.mean(R))}


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

    Loudness and roughness are computed in parallel (both >100ms).
    Sharpness is computed after loudness since it depends on loudness output.

    All metrics use relative values (calib=1.0) since we don't have
    calibrated SPL measurements.

    Args:
        y: Audio signal (mono or stereo).
        sr: Sample rate.

    Returns:
        Dictionary with psychoacoustic metrics, or None if MoSQITo unavailable.
        Keys: loudness_sone, loudness_sone_max, sharpness_acum, roughness_asper
    """
    # Lazy import - MoSQITo is optional (check before spawning processes)
    try:
        from mosqito.sq_metrics import sharpness_din_from_loudness
    except ImportError:
        logger.debug("MoSQITo not installed - skipping psychoacoustic metrics")
        return None

    try:
        # Preprocess to 48kHz mono (resample once, pass to both metrics)
        y_48k, fs = prepare_for_mosqito(y, sr)

        # Check for very short or silent audio
        if len(y_48k) < 4800:  # Less than 0.1 seconds at 48kHz
            logger.warning("Audio too short for psychoacoustic analysis")
            return None

        if np.max(np.abs(y_48k)) < 1e-10:
            logger.warning("Audio is silent - skipping psychoacoustic analysis")
            return None

        # Parallel computation of loudness and roughness
        # Loudness: ~900ms, Roughness: ~200-300ms (independent, CPU-bound)
        try:
            with ProcessPoolExecutor(max_workers=2) as executor:
                loudness_future = executor.submit(_compute_loudness, y_48k, fs)
                roughness_future = executor.submit(_compute_roughness, y_48k, fs)

                loudness_result = loudness_future.result()
                roughness_result = roughness_future.result()
        except Exception as e:
            # Fall back to serial if parallelization fails
            logger.warning(f"Parallel computation failed, falling back to serial: {e}")
            loudness_result = _compute_loudness(y_48k, fs)
            roughness_result = _compute_roughness(y_48k, fs)

        # Sharpness depends on loudness output, compute serially (<1ms)
        S = sharpness_din_from_loudness(
            loudness_result["N"], loudness_result["N_spec"], weighting="din"
        )

        return {
            "loudness_sone": loudness_result["loudness_sone"],
            "loudness_sone_max": loudness_result["loudness_sone_max"],
            "sharpness_acum": float(np.mean(S)),
            "roughness_asper": roughness_result["roughness_asper"],
        }

    except Exception as e:
        # MoSQITo can fail on edge cases (very short audio, unusual content)
        logger.warning(f"Psychoacoustic analysis failed: {e}")
        return None
