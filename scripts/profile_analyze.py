#!/usr/bin/env python3
"""Profile the analyze pipeline to identify performance bottlenecks.

This script profiles the full analyze() function using cProfile
to identify hotspots in the audio analysis pipeline.
"""

import cProfile
import pstats
import io
import time
from pathlib import Path

# Add src to path for development
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from audioloop.analyze import analyze


def profile_analyze(wav_path: str, num_runs: int = 1):
    """Profile the analyze function on a WAV file.

    Args:
        wav_path: Path to WAV file
        num_runs: Number of runs (default 1 for profiling)
    """
    path = Path(wav_path)

    print(f"Profiling analyze() on: {path}")
    print(f"File exists: {path.exists()}")
    print("-" * 60)

    # Create profiler
    profiler = cProfile.Profile()

    # Time the overall execution
    start = time.perf_counter()

    profiler.enable()
    for _ in range(num_runs):
        result = analyze(path)
    profiler.disable()

    elapsed = time.perf_counter() - start

    print(f"\nTotal time: {elapsed:.3f}s ({num_runs} run{'s' if num_runs > 1 else ''})")
    print(f"Average per run: {elapsed/num_runs:.3f}s")
    print("-" * 60)

    # Print top functions by cumulative time
    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.sort_stats('cumulative')
    stats.print_stats(30)
    print(stream.getvalue())

    # Also print top by internal time (tottime)
    print("\n" + "=" * 60)
    print("TOP 20 BY INTERNAL TIME (tottime):")
    print("=" * 60)

    stream2 = io.StringIO()
    stats2 = pstats.Stats(profiler, stream=stream2)
    stats2.sort_stats('tottime')
    stats2.print_stats(20)
    print(stream2.getvalue())

    # Return result for verification
    return result, elapsed


def profile_components(wav_path: str):
    """Profile individual components of the pipeline separately."""
    import librosa
    import numpy as np

    path = Path(wav_path)

    print("\n" + "=" * 60)
    print("COMPONENT-LEVEL TIMING:")
    print("=" * 60)

    # 1. Load audio
    start = time.perf_counter()
    y, sr = librosa.load(str(path), sr=None, mono=False)
    load_time = time.perf_counter() - start
    print(f"librosa.load: {load_time*1000:.1f}ms")

    # 2. Spectral features (simulate what analyze does)
    if y.ndim == 1:
        left = y
    else:
        left = y[0]

    start = time.perf_counter()
    from audioloop.analyze import _compute_spectral_features
    _compute_spectral_features(left, sr)
    spectral_time = time.perf_counter() - start
    print(f"_compute_spectral_features: {spectral_time*1000:.1f}ms")

    # 3. Temporal features
    start = time.perf_counter()
    from audioloop.analyze import _compute_temporal_features
    combined = y if y.ndim == 1 else np.mean(y, axis=0)
    _compute_temporal_features(combined, sr)
    temporal_time = time.perf_counter() - start
    print(f"_compute_temporal_features: {temporal_time*1000:.1f}ms")

    # 4. LUFS loudness
    start = time.perf_counter()
    from audioloop.analyze import _compute_loudness_lufs
    _compute_loudness_lufs(y, sr)
    lufs_time = time.perf_counter() - start
    print(f"_compute_loudness_lufs: {lufs_time*1000:.1f}ms")

    # 5. Psychoacoustic (the slow part)
    start = time.perf_counter()
    from audioloop.psychoacoustic import compute_psychoacoustic
    compute_psychoacoustic(y, sr)
    psychoacoustic_time = time.perf_counter() - start
    print(f"compute_psychoacoustic (TOTAL): {psychoacoustic_time*1000:.1f}ms")

    # Break down psychoacoustic further
    print("\n  Psychoacoustic breakdown:")

    from audioloop.psychoacoustic import prepare_for_mosqito

    start = time.perf_counter()
    y_48k, fs = prepare_for_mosqito(y, sr)
    resample_time = time.perf_counter() - start
    print(f"    prepare_for_mosqito (resample): {resample_time*1000:.1f}ms")

    try:
        from mosqito.sq_metrics import loudness_zwtv, roughness_dw, sharpness_din_from_loudness

        start = time.perf_counter()
        N, N_spec, bark_axis, time_axis = loudness_zwtv(y_48k, fs=fs, field_type="free")
        loudness_time = time.perf_counter() - start
        print(f"    loudness_zwtv: {loudness_time*1000:.1f}ms")

        start = time.perf_counter()
        S = sharpness_din_from_loudness(N, N_spec, weighting="din")
        sharpness_time = time.perf_counter() - start
        print(f"    sharpness_din_from_loudness: {sharpness_time*1000:.1f}ms")

        start = time.perf_counter()
        R, time_axis_r, _, _ = roughness_dw(y_48k, fs=fs)
        roughness_time = time.perf_counter() - start
        print(f"    roughness_dw: {roughness_time*1000:.1f}ms")

        # Summary
        total_mosqito = loudness_time + sharpness_time + roughness_time
        total_librosa = load_time + spectral_time + temporal_time + lufs_time
        total = total_librosa + psychoacoustic_time

        print("\n" + "-" * 40)
        print("SUMMARY:")
        print(f"  librosa/basic features: {total_librosa*1000:.1f}ms ({100*total_librosa/total:.1f}%)")
        print(f"  MoSQITo metrics: {total_mosqito*1000:.1f}ms ({100*total_mosqito/total:.1f}%)")
        print(f"    - loudness_zwtv: {loudness_time*1000:.1f}ms")
        print(f"    - roughness_dw: {roughness_time*1000:.1f}ms")
        print(f"    - sharpness_din: {sharpness_time*1000:.1f}ms")
        print(f"  TOTAL: {total*1000:.1f}ms")

    except ImportError:
        print("  MoSQITo not installed - cannot profile psychoacoustic components")


if __name__ == "__main__":
    # Default to test fixture
    default_path = Path(__file__).parent.parent / "tests" / "fixtures" / "test_tone.wav"

    if len(sys.argv) > 1:
        wav_path = sys.argv[1]
    else:
        wav_path = str(default_path)

    # Run profiler
    result, elapsed = profile_analyze(wav_path)

    # Run component-level timing
    profile_components(wav_path)

    print("\n" + "=" * 60)
    print("Analysis result psychoacoustic metrics:")
    print(result.psychoacoustic)
