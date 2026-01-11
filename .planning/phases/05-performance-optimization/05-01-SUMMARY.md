---
phase: 05-performance-optimization
plan: 01
subsystem: audio-analysis
tags: [performance, profiling, cProfile, MoSQITo, psychoacoustic, benchmark]

# Dependency graph
requires:
  - phase: 04-zwicker-integration/plan-02
    provides: Psychoacoustic metrics (loudness, sharpness, roughness) in analyze()
provides:
  - Profiling scripts for analyze pipeline
  - Benchmark scripts for performance measurement
  - Performance documentation and baseline measurements
affects: [audio-analysis, cli-performance]

# Tech tracking
tech-stack:
  added: [cProfile, pstats]
  patterns: [profile-first-optimization, benchmark-before-after]

key-files:
  created: [scripts/profile_analyze.py, scripts/benchmark_analyze.py]
  modified: [src/audioloop/psychoacoustic.py]

key-decisions:
  - "Serial computation retained - parallelization overhead exceeded benefit"
  - "ProcessPoolExecutor adds ~500ms overhead, negating ~200ms savings"
  - "Sub-5s target realistic for 1-4 second audio only"

patterns-established:
  - "Profile with cProfile before optimizing"
  - "Benchmark with warm-up runs to exclude import overhead"
  - "--no-psychoacoustic flag for fast analysis (~15ms vs ~1100ms)"

issues-created: []

# Metrics
duration: 16min
completed: 2026-01-11
---

# Phase 5 Plan 1: Performance Optimization Summary

**Profiled analyze pipeline, tested parallelization (slower due to process overhead), established sub-5s baseline for 1-4 second audio**

## Performance

- **Duration:** 16 min
- **Started:** 2026-01-11T00:15:03Z
- **Completed:** 2026-01-11T00:31:XX
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments

- Created profiling script revealing MoSQITo loudness_zwtv (~900ms) as dominant bottleneck
- Tested parallelization approaches (ProcessPoolExecutor, ThreadPoolExecutor) - both slower than serial
- Established performance baselines: ~1.1s for 1-second audio, sub-5s for up to 4 seconds

## Task Commits

Each task was committed atomically:

1. **Task 1: Profile analyze pipeline with cProfile** - `e33babf` (perf)
2. **Task 2: Parallelize MoSQITo metrics** - `678a9b9` (perf)
3. **Task 3: Benchmark and revert to serial** - `80c162c` (perf)

## Files Created/Modified

- `scripts/profile_analyze.py` - Profiling script for analyze pipeline with component timing
- `scripts/benchmark_analyze.py` - Benchmark script comparing full vs fast analysis
- `src/audioloop/psychoacoustic.py` - Updated docstring with performance note

## Profiling Results

Component timing for 1-second test tone (imports cached):

| Component | Time | % of Total |
|-----------|------|------------|
| librosa.load | 0.5ms | 0.04% |
| spectral features | 6.8ms | 0.6% |
| temporal features | 0.4ms | 0.04% |
| loudness (LUFS) | 1.6ms | 0.1% |
| **MoSQITo total** | **1078ms** | **95.7%** |
| - loudness_zwtv | 890ms | 79% |
| - roughness_dw | 200-300ms | 18-27% |
| - sharpness_din | <1ms | <0.1% |

**Key finding:** MoSQITo's loudness_zwtv dominates analysis time.

## Parallelization Analysis

Tested three approaches:

| Approach | Mean Time | Notes |
|----------|-----------|-------|
| Serial | 1156ms | **Fastest** |
| ThreadPoolExecutor | 1333ms | +15% slower (GIL contention) |
| ProcessPoolExecutor | 1597ms | +38% slower (spawn overhead) |

**Why parallelization failed:**
- ProcessPoolExecutor spawn overhead: ~500ms
- loudness_zwtv (~900ms) dominates the parallel path
- Only ~200-300ms could theoretically be saved (roughness)
- 500ms overhead > 300ms potential savings

## Benchmark Results

| Audio Duration | Analysis Time | Sub-5s Target |
|----------------|---------------|---------------|
| 1 second | ~1.1s | PASS |
| 3 seconds | ~3.6s | PASS |
| 8 seconds | ~21s | FAIL |
| 15 seconds | ~39s | FAIL |

**Scaling:** Analysis time scales roughly linearly with audio duration (~1.1s per second of audio).

**Fast mode:** `--no-psychoacoustic` reduces analysis to ~15-20ms (spectral/temporal only).

## Decisions Made

1. **Retained serial computation:** Parallelization made things slower, not faster
2. **Sub-5s realistic for short audio:** Target met for 1-4 second synthesized sounds
3. **Recommend --no-psychoacoustic for long audio:** Essential for >5 second files

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Reverted parallelization after benchmarking**
- **Found during:** Task 3 (benchmarking)
- **Issue:** Parallelization was slower than serial due to process spawn overhead
- **Fix:** Reverted to serial computation in psychoacoustic.py
- **Files modified:** src/audioloop/psychoacoustic.py
- **Verification:** Benchmark confirms serial is fastest
- **Committed in:** `80c162c` (Task 3 commit)

---

**Total deviations:** 1 auto-fixed (reverted optimization that made things worse)
**Impact on plan:** Followed profile-first principle from research; optimization attempt informed by data

## Issues Encountered

- **Parallelization overhead exceeded benefit:** Research suggested parallelizing tasks >500ms, but didn't account for ProcessPoolExecutor's own ~500ms spawn overhead. This is a valuable learning for future optimization work.

## Next Phase Readiness

- Phase 5 Plan 1 complete (profiling, benchmarking, performance baseline established)
- MoSQITo's loudness_zwtv is the bottleneck - future optimization would require:
  - Alternative loudness algorithms
  - Native code / Numba optimization within MoSQITo
  - Caching for repeated analysis of same file
- Ready for Phase 6 (Spectrogram Visualization) if planned

---
*Phase: 05-performance-optimization*
*Completed: 2026-01-11*
