---
phase: 04-zwicker-integration
plan: 01
subsystem: analysis
tags: [mosqito, zwicker, psychoacoustics, loudness, sharpness, roughness]

# Dependency graph
requires:
  - phase: 02-analysis-core
    provides: analyze() function and AnalysisResult dataclass
provides:
  - compute_psychoacoustic() function for Zwicker metrics
  - psychoacoustic field in AnalysisResult with loudness/sharpness/roughness
  - Optional [psychoacoustic] dependency for MoSQITo
affects: [compare, interpret, future psychoacoustic features]

# Tech tracking
tech-stack:
  added: [mosqito>=1.2.0]
  patterns: [lazy-import-optional-dependency, graceful-fallback]

key-files:
  created: [src/audioloop/psychoacoustic.py]
  modified: [src/audioloop/analyze.py, pyproject.toml, tests/test_analyze.py]

key-decisions:
  - "Use direct MoSQITo function API (loudness_zwtv, sharpness_din_from_loudness, roughness_dw) instead of Audio class"
  - "Lazy import MoSQITo at call time for graceful fallback when not installed"
  - "Preprocess all audio to 48kHz mono float32 before MoSQITo analysis"
  - "Return empty dict (not None) from analyze() when MoSQITo unavailable"

patterns-established:
  - "Optional dependency pattern: lazy import with graceful fallback to None/empty"
  - "Audio preprocessing pipeline: resample then mono-mix then dtype cast"

issues-created: []

# Metrics
duration: 5min
completed: 2026-01-09
---

# Phase 4 Plan 1: Psychoacoustic Metrics Summary

**MoSQITo-based Zwicker loudness, sharpness, and roughness integrated into analyze() output with graceful optional-dependency fallback**

## Performance

- **Duration:** 5 min
- **Started:** 2026-01-09T21:44:39Z
- **Completed:** 2026-01-09T21:50:04Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Created psychoacoustic.py module with prepare_for_mosqito() and compute_psychoacoustic() functions
- Integrated psychoacoustic metrics into AnalysisResult dataclass and JSON output
- Added mosqito>=1.2.0 as optional [psychoacoustic] dependency
- All 18 tests pass including 4 new psychoacoustic tests

## Task Commits

Each task was committed atomically:

1. **Task 1: Create psychoacoustic.py module** - `21568df` (feat)
2. **Task 2: Integrate into AnalysisResult** - `ac22898` (feat)

## Files Created/Modified

- `src/audioloop/psychoacoustic.py` - New module with MoSQITo wrapper functions
- `src/audioloop/analyze.py` - Added psychoacoustic field and import
- `pyproject.toml` - Added [psychoacoustic] optional dependency
- `tests/test_analyze.py` - Added TestPsychoacoustic class with 4 tests

## Decisions Made

- **Direct function API over Audio class:** The loudness_zwtv(), sharpness_din_from_loudness(), roughness_dw() functions are simpler than MoSQITo's Audio class for our single-file use case
- **weighting="din" parameter:** Research doc had is_stationary which doesn't exist in MoSQITo 1.2.1 API; corrected to weighting="din"
- **Graceful empty dict:** analyze() returns psychoacoustic={} (not None) when MoSQITo unavailable for consistent JSON structure

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed MoSQITo API mismatch for sharpness function**
- **Found during:** Task 2 (Integration testing)
- **Issue:** Research doc specified is_stationary=False parameter but MoSQITo 1.2.1 uses weighting="din" instead
- **Fix:** Changed sharpness_din_from_loudness(N, N_spec, is_stationary=False) to sharpness_din_from_loudness(N, N_spec, weighting="din")
- **Files modified:** src/audioloop/psychoacoustic.py
- **Verification:** Test file produces valid psychoacoustic metrics
- **Committed in:** ac22898 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (API bug from outdated research)
**Impact on plan:** Minor correction, no scope change

## Issues Encountered

None - plan executed smoothly after API correction.

## Next Phase Readiness

- Psychoacoustic metrics integrated and working
- Ready for any remaining Phase 4 plans or Phase 5
- Consider adding --no-psychoacoustic flag if performance becomes an issue (MoSQITo is slow for long files)

---
*Phase: 04-zwicker-integration*
*Completed: 2026-01-09*
