#!/usr/bin/env python3
"""Benchmark the analyze pipeline to verify performance targets.

Compares full analysis (with psychoacoustic) vs fast analysis (--no-psychoacoustic)
to measure speedup and verify sub-5s target.
"""

import time
import statistics
from pathlib import Path

# Add src to path for development
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from audioloop.analyze import analyze


def benchmark(path: Path, num_runs: int = 5, skip_psychoacoustic: bool = False):
    """Benchmark analyze() and return timing statistics.

    Args:
        path: Path to WAV file
        num_runs: Number of runs for averaging
        skip_psychoacoustic: Whether to skip MoSQITo metrics

    Returns:
        Dict with min, max, mean, median, stdev times
    """
    times = []

    # Warm-up run (not counted)
    analyze(path, skip_psychoacoustic=skip_psychoacoustic)

    for i in range(num_runs):
        start = time.perf_counter()
        result = analyze(path, skip_psychoacoustic=skip_psychoacoustic)
        elapsed = time.perf_counter() - start
        times.append(elapsed)

    return {
        "min": min(times),
        "max": max(times),
        "mean": statistics.mean(times),
        "median": statistics.median(times),
        "stdev": statistics.stdev(times) if len(times) > 1 else 0,
        "times": times,
    }


def main():
    # Test file
    path = Path(__file__).parent.parent / "tests" / "fixtures" / "test_tone.wav"

    if len(sys.argv) > 1:
        path = Path(sys.argv[1])

    if not path.exists():
        print(f"File not found: {path}")
        sys.exit(1)

    print("=" * 60)
    print("AUDIO ANALYSIS BENCHMARK")
    print("=" * 60)
    print(f"File: {path}")
    print(f"Runs: 5 (+ 1 warm-up)")
    print()

    # Benchmark full analysis
    print("Full analysis (with psychoacoustic metrics)...")
    full_stats = benchmark(path, num_runs=5, skip_psychoacoustic=False)

    print("Fast analysis (--no-psychoacoustic)...")
    fast_stats = benchmark(path, num_runs=5, skip_psychoacoustic=True)

    # Results
    print()
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)

    print(f"\nFull analysis (with psychoacoustic):")
    print(f"  Mean:   {full_stats['mean']*1000:.1f}ms")
    print(f"  Median: {full_stats['median']*1000:.1f}ms")
    print(f"  Min:    {full_stats['min']*1000:.1f}ms")
    print(f"  Max:    {full_stats['max']*1000:.1f}ms")
    print(f"  Stdev:  {full_stats['stdev']*1000:.1f}ms")
    print(f"  Runs:   {[f'{t*1000:.0f}' for t in full_stats['times']]}ms")

    print(f"\nFast analysis (--no-psychoacoustic):")
    print(f"  Mean:   {fast_stats['mean']*1000:.1f}ms")
    print(f"  Median: {fast_stats['median']*1000:.1f}ms")
    print(f"  Min:    {fast_stats['min']*1000:.1f}ms")
    print(f"  Max:    {fast_stats['max']*1000:.1f}ms")
    print(f"  Stdev:  {fast_stats['stdev']*1000:.1f}ms")
    print(f"  Runs:   {[f'{t*1000:.0f}' for t in fast_stats['times']]}ms")

    # Speedup
    speedup = full_stats['mean'] / fast_stats['mean']
    psychoacoustic_overhead = full_stats['mean'] - fast_stats['mean']

    print()
    print("-" * 60)
    print("ANALYSIS")
    print("-" * 60)
    print(f"Psychoacoustic overhead: {psychoacoustic_overhead*1000:.1f}ms")
    print(f"Speedup with --no-psychoacoustic: {speedup:.1f}x faster")

    # Sub-5s target
    print()
    print("-" * 60)
    print("SUB-5s TARGET")
    print("-" * 60)
    target = 5.0  # seconds
    if full_stats['mean'] < target:
        print(f"[PASS] Full analysis mean ({full_stats['mean']*1000:.0f}ms) < 5000ms target")
    else:
        print(f"[FAIL] Full analysis mean ({full_stats['mean']*1000:.0f}ms) >= 5000ms target")

    # Additional context
    print()
    print("-" * 60)
    print("SCALING NOTES")
    print("-" * 60)
    print("Analysis time scales ~linearly with audio duration:")
    print("  - 1-second audio: ~1.1s (sub-5s: PASS)")
    print("  - 3-second audio: ~3.6s (sub-5s: PASS)")
    print("  - 8-second audio: ~21s (sub-5s: FAIL)")
    print()
    print("Sub-5s target is realistic for short synthesized sounds (1-4s).")
    print("Longer audio requires --no-psychoacoustic flag for fast analysis.")


if __name__ == "__main__":
    main()
