# Phase 5: Performance Optimization - Research

**Researched:** 2026-01-09
**Domain:** Python profiling and parallel audio analysis
**Confidence:** HIGH

<research_summary>
## Summary

Researched Python profiling tools and parallel processing patterns for optimizing the audio analysis pipeline. The current `analyze` function runs librosa spectral analysis and MoSQITo psychoacoustic metrics serially. The phase goal is sub-5s full analysis.

Key finding: The three MoSQITo computations (loudness, sharpness, roughness) are independent and CPU-bound. ProcessPoolExecutor is the right tool since NumPy/SciPy release the GIL, but process spawning overhead matters - only worth parallelizing if each task takes >500ms. Profiling must come first to identify actual bottlenecks.

**Primary recommendation:** Profile with cProfile first to find hotspots, then parallelize MoSQITo metrics with ProcessPoolExecutor if they dominate. Avoid parallelizing librosa spectral features (too fast, overhead dominates).
</research_summary>

<standard_stack>
## Standard Stack

### Profiling Tools
| Tool | Version | Purpose | Why Standard |
|------|---------|---------|--------------|
| cProfile | stdlib | Function-level profiling | Built-in, low overhead, first-pass analysis |
| line_profiler | 4.1+ | Line-level profiling | Pinpoint exact lines in hotspot functions |
| py-spy | 0.3+ | Production profiling | Attach to running process, no code changes |

### Parallelization
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| concurrent.futures | stdlib | High-level parallelism | Built-in, clean API, ProcessPoolExecutor |
| multiprocessing | stdlib | Process-based parallelism | Lower-level control if needed |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| joblib | 1.3+ | Parallel loops | If need chunking or Dask backend |
| tqdm | 4.66+ | Progress bars | User feedback during analysis |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| ProcessPoolExecutor | ThreadPoolExecutor | Threads only work if code releases GIL - NumPy/librosa do, but safer with processes |
| ProcessPoolExecutor | joblib.Parallel | joblib adds dependency, slightly nicer API for loops |
| cProfile | Scalene | Scalene does CPU+memory but adds dependency |

**Installation:**
```bash
pip install line-profiler  # Optional, for deep analysis
pip install py-spy         # Optional, for production profiling
# concurrent.futures and cProfile are stdlib
```
</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Recommended Profiling Workflow
```
1. cProfile: Identify slow functions (80/20 rule)
2. line_profiler: Drill into hotspot functions
3. Measure baseline with real audio files
4. Optimize
5. Measure again to verify
```

### Pattern 1: Profile-First Optimization
**What:** Always profile before optimizing
**When to use:** Every optimization task
**Example:**
```python
# Profile the analyze function
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()
result = analyze(path)
profiler.disable()

stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)  # Top 20 by cumulative time
```

### Pattern 2: ProcessPoolExecutor for Independent Tasks
**What:** Parallelize independent, CPU-bound computations
**When to use:** Tasks >500ms each, no shared state
**Example:**
```python
# Source: Python docs concurrent.futures
from concurrent.futures import ProcessPoolExecutor

def compute_loudness(y, sr):
    # MoSQITo loudness computation
    ...

def compute_roughness(y, sr):
    # MoSQITo roughness computation
    ...

# Parallelize independent MoSQITo metrics
with ProcessPoolExecutor(max_workers=3) as executor:
    futures = {
        'loudness': executor.submit(compute_loudness, y, sr),
        'roughness': executor.submit(compute_roughness, y, sr),
        'sharpness': executor.submit(compute_sharpness, y, sr),
    }
    results = {k: f.result() for k, f in futures.items()}
```

### Pattern 3: Chunking for Small Tasks
**What:** Batch small tasks to amortize process overhead
**When to use:** Many small tasks (<100ms each)
**Example:**
```python
# Don't: One process per feature (overhead dominates)
# Do: Chunk features into batches per process

def analyze_batch(audio_paths):
    return [analyze_single(p) for p in audio_paths]

# Split files into chunks matching worker count
chunks = [paths[i::n_workers] for i in range(n_workers)]
with ProcessPoolExecutor(max_workers=n_workers) as executor:
    results = list(executor.map(analyze_batch, chunks))
```

### Anti-Patterns to Avoid
- **Optimizing without profiling:** Chasing wrong bottleneck
- **ThreadPoolExecutor for CPU-bound:** GIL blocks true parallelism
- **Parallelizing fast operations:** Process overhead > computation time
- **Shared mutable state between processes:** Race conditions, slow pickling
</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Process management | Manual subprocess/fork | ProcessPoolExecutor | Context manager, exception handling, cleanup |
| Profiling | Manual timing with time.time() | cProfile | Miss nested calls, inaccurate |
| Inter-process data | Custom IPC | Return values from futures | Pickling handled automatically |
| Progress tracking | Print statements | tqdm | Cleaner UX, ETA calculation |

**Key insight:** Python's standard library already provides battle-tested parallelization primitives. ProcessPoolExecutor handles process lifecycle, exception propagation, and resource cleanup. Rolling your own leads to subtle bugs around process cleanup and signal handling.
</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Parallelizing Fast Operations
**What goes wrong:** ProcessPoolExecutor makes code slower, not faster
**Why it happens:** Process spawn + pickle overhead (50-200ms) exceeds task time
**How to avoid:** Only parallelize tasks >500ms each; profile first
**Warning signs:** Parallel version slower than serial; CPU cores underutilized

### Pitfall 2: Pickling Large Arrays
**What goes wrong:** Huge slowdown when passing numpy arrays between processes
**Why it happens:** Arrays must be pickled/unpickled for IPC, up to 4x slower
**How to avoid:** Pass file paths instead of data; load in worker; or use shared memory
**Warning signs:** Memory spikes during parallel execution; slow submit() calls

### Pitfall 3: Oversubscription
**What goes wrong:** More workers than CPU cores causes thrashing
**Why it happens:** Default max_workers can exceed physical cores
**How to avoid:** Set max_workers to os.cpu_count() or less
**Warning signs:** CPU at 100% but work not progressing; high context switching

### Pitfall 4: GIL Contention with ThreadPoolExecutor
**What goes wrong:** No speedup despite multiple threads
**Why it happens:** CPU-bound Python code holds GIL; threads can't run in parallel
**How to avoid:** Use ProcessPoolExecutor for CPU-bound; ThreadPoolExecutor for I/O
**Warning signs:** All threads waiting; single core at 100%

### Pitfall 5: Not Measuring Before/After
**What goes wrong:** No idea if optimization actually helped
**Why it happens:** Assumption-based optimization without baseline
**How to avoid:** Always measure with cProfile or timing before AND after changes
**Warning signs:** Can't quantify improvement; "feels faster" is not data
</common_pitfalls>

<code_examples>
## Code Examples

Verified patterns for this project:

### Profiling analyze() Function
```python
# Source: Python docs profile module
import cProfile
import pstats
from pathlib import Path
from audioloop.analyze import analyze

def profile_analyze(wav_path: str):
    """Profile the full analysis pipeline."""
    profiler = cProfile.Profile()
    profiler.enable()

    result = analyze(Path(wav_path))

    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(30)

    return result

# Usage: profile_analyze("test.wav")
```

### Parallel MoSQITo Metrics (If Profiling Shows Bottleneck)
```python
# Source: concurrent.futures docs + MoSQITo usage
from concurrent.futures import ProcessPoolExecutor
import numpy as np

def _compute_loudness(y_48k: np.ndarray, fs: int) -> dict:
    """Compute loudness in subprocess."""
    from mosqito.sq_metrics import loudness_zwtv
    N, N_spec, _, _ = loudness_zwtv(y_48k, fs=fs, field_type="free")
    return {
        "loudness_sone": float(np.mean(N)),
        "loudness_sone_max": float(np.max(N)),
        "N": N,  # Needed for sharpness
        "N_spec": N_spec,
    }

def _compute_roughness(y_48k: np.ndarray, fs: int) -> dict:
    """Compute roughness in subprocess."""
    from mosqito.sq_metrics import roughness_dw
    R, _, _, _ = roughness_dw(y_48k, fs=fs)
    return {"roughness_asper": float(np.mean(R))}

def compute_psychoacoustic_parallel(y: np.ndarray, sr: int) -> dict:
    """Parallel version - use only if profiling shows benefit."""
    y_48k, fs = prepare_for_mosqito(y, sr)

    with ProcessPoolExecutor(max_workers=2) as executor:
        loudness_future = executor.submit(_compute_loudness, y_48k, fs)
        roughness_future = executor.submit(_compute_roughness, y_48k, fs)

        loudness_result = loudness_future.result()
        roughness_result = roughness_future.result()

    # Sharpness depends on loudness output, compute serially
    from mosqito.sq_metrics import sharpness_din_from_loudness
    S = sharpness_din_from_loudness(
        loudness_result["N"],
        loudness_result["N_spec"],
        weighting="din"
    )

    return {
        "loudness_sone": loudness_result["loudness_sone"],
        "loudness_sone_max": loudness_result["loudness_sone_max"],
        "sharpness_acum": float(np.mean(S)),
        "roughness_asper": roughness_result["roughness_asper"],
    }
```

### Using line_profiler for Deep Analysis
```python
# Source: line_profiler docs
# Install: pip install line_profiler

# In code, decorate functions to profile:
# @profile
# def compute_psychoacoustic(y, sr):
#     ...

# Run with:
# kernprof -l -v script.py
```
</code_examples>

<sota_updates>
## State of the Art (2025-2026)

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| multiprocessing.Pool | ProcessPoolExecutor | 2015+ | Cleaner API, better exception handling |
| Manual timing | cProfile + line_profiler | Always | Accurate, reveals nested calls |
| GIL workarounds | Free-threaded Python 3.13 | 2024 | Experimental; NumPy 2.1+/SciPy 1.15+ support |

**New tools/patterns to consider:**
- **py-spy:** Attach to running processes, flame graphs, minimal overhead
- **Scalene:** Combined CPU+memory+GPU profiling in one tool
- **Python 3.13 free-threading:** Experimental GIL-free mode (not production-ready)

**Deprecated/outdated:**
- **multiprocessing.Pool:** Still works but ProcessPoolExecutor is preferred
- **Manual fork/subprocess:** Error-prone, use concurrent.futures instead
</sota_updates>

<open_questions>
## Open Questions

1. **MoSQITo individual metric timing**
   - What we know: Three metrics computed serially (loudness, sharpness, roughness)
   - What's unclear: How long each takes individually
   - Recommendation: Profile with cProfile first; if one dominates, focus there

2. **Sharpness dependency on loudness**
   - What we know: `sharpness_din_from_loudness` requires loudness output
   - What's unclear: Can we restructure to parallelize?
   - Recommendation: Accept sharpness as serial; parallelize loudness+roughness only

3. **librosa resampling overhead**
   - What we know: MoSQITo needs 48kHz; librosa.resample called in prepare_for_mosqito
   - What's unclear: How much time resampling consumes
   - Recommendation: Profile; if significant, resample once and pass to all metrics
</open_questions>

<sources>
## Sources

### Primary (HIGH confidence)
- [Python concurrent.futures docs](https://docs.python.org/3/library/concurrent.futures.html) - ProcessPoolExecutor patterns
- [Python profile docs](https://docs.python.org/3/library/profile.html) - cProfile usage
- [NumPy thread safety](https://numpy.org/doc/stable/reference/thread_safety.html) - GIL release behavior
- [SciPy thread safety](https://docs.scipy.org/doc/scipy/tutorial/thread_safety.html) - Safe parallel usage

### Secondary (MEDIUM confidence)
- [OneUpTime Python profiling guide](https://oneuptime.com/blog/post/2025-01-06-profile-python-cprofile-pyspy/view) - cProfile + py-spy workflow
- [Real Python profiling](https://realpython.com/python-profiling/) - Best practices, 80/20 rule
- [Super Fast Python - NumPy vs GIL](https://superfastpython.com/numpy-vs-gil/) - When processes beat threads

### Tertiary (LOW confidence - needs validation)
- GitHub gist tracek/librosa_parallel - Parallelization pattern, warns about oversubscription
- MoSQITo GitHub - Dependencies verified (numpy, scipy, pyuff), no thread safety docs found
</sources>

<metadata>
## Metadata

**Research scope:**
- Core technology: Python profiling, concurrent.futures
- Ecosystem: cProfile, line_profiler, ProcessPoolExecutor
- Patterns: Profile-first optimization, parallel independent tasks
- Pitfalls: Overhead, pickling, oversubscription, GIL

**Confidence breakdown:**
- Standard stack: HIGH - Python stdlib, well-documented
- Architecture: HIGH - Standard patterns from official docs
- Pitfalls: HIGH - Well-known Python parallelization issues
- Code examples: HIGH - Based on official documentation

**Research date:** 2026-01-09
**Valid until:** 2026-03-09 (60 days - stable Python stdlib)
</metadata>

---

*Phase: 05-performance-optimization*
*Research completed: 2026-01-09*
*Ready for planning: yes*
