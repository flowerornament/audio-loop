---
phase: 01-render-pipeline
plan: 01
subsystem: cli
tags: [supercollider, sclang, nrt, typer, cli, audio-rendering]

# Dependency graph
requires: []
provides:
  - audioloop CLI entry point
  - audioloop render command (full NRT + wrapped function modes)
  - SC path discovery with env var override
  - sclang subprocess execution with timeout
  - SC error detection and parsing
  - NRT wrapper for simple function syntax
affects: [02-analysis-core, 03-iteration-tools]

# Tech tracking
tech-stack:
  added: [typer, rich, pytest]
  patterns: [CLI with typer, subprocess management, NRT rendering]

key-files:
  created:
    - src/audioloop/cli.py
    - src/audioloop/render.py
    - src/audioloop/sclang.py
    - src/audioloop/sc_paths.py
    - src/audioloop/errors.py
    - src/audioloop/wrapper.py
    - tests/test_render.py
    - tests/test_wrapper.py
  modified: []

key-decisions:
  - "Two render modes: full NRT (Claude writes complete script) and wrapped (Claude writes just function)"
  - "Mode detection via presence of recordNRT in source"
  - "__OUTPUT_PATH__ placeholder convention for output path injection"
  - "Exit codes: 0=success, 1=SC error, 2=system error"

patterns-established:
  - "Use uv for package management"
  - "sclang subprocess with cwd=SC MacOS dir"
  - "Output paths must be absolute for sclang"

issues-created: []

# Metrics
duration: ~25min
completed: 2026-01-09
---

# Phase 1 Plan 01: Render Pipeline Summary

**CLI tool for rendering SuperCollider code to WAV files with full NRT and wrapped function modes, error detection, and JSON output for Claude parsing**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-01-09T11:20:00Z
- **Completed:** 2026-01-09T11:45:00Z
- **Tasks:** 9 + 1 checkpoint
- **Files created:** 18
- **Tests:** 24 passing

## Accomplishments

- `audioloop render` command with two modes (full NRT + wrapped function)
- Mode detection via `recordNRT` presence in source code
- `__OUTPUT_PATH__` placeholder convention for output path injection
- `--duration` flag for wrapped function mode
- sclang subprocess management with timeout handling
- SC error detection and structured parsing
- JSON output format for Claude integration
- 24 pytest tests covering both render modes and edge cases

## Task Commits

Each task was committed atomically:

1. **Task 1: Project Setup** - `6f6a76b` (feat)
2. **Task 2: SC Path Discovery** - `a561eb5` (feat)
3. **Task 3: sclang Subprocess Execution** - `0f4e035` (feat)
4. **Task 4: Error Detection** - `5d12c36` (feat)
5. **Task 5: NRT Wrapper Module** - `01bb55a` (feat)
6. **Task 6: Render Command Implementation** - `1feb029` (feat)
7. **Task 7: Test SC Scripts** - `9d917cf` (test)
8. **Task 8: Integration Tests** - `cd5a9af` (test)
9. **Task 9: CLI Polish** - `33aca07` (chore)

**Bug fix during checkpoint:** `2cf66af` (fix) - output path resolution

## Files Created/Modified

**Source:**
- `src/audioloop/__init__.py` - Package init with version
- `src/audioloop/cli.py` - CLI entry point with render command
- `src/audioloop/render.py` - Core render logic
- `src/audioloop/sclang.py` - sclang subprocess execution
- `src/audioloop/sc_paths.py` - SC installation path discovery
- `src/audioloop/errors.py` - SC error detection and parsing
- `src/audioloop/wrapper.py` - NRT wrapping for simple functions

**Tests:**
- `tests/test_render.py` - 11 integration tests
- `tests/test_wrapper.py` - 13 unit tests
- `tests/fixtures/*.scd` - 4 test fixtures

**Config:**
- `pyproject.toml` - Project configuration

## Decisions Made

1. **Two render modes** - Full NRT for complex sounds, wrapped for quick iteration
2. **Mode detection** - Check for `recordNRT` in source (simple, reliable)
3. **Placeholder convention** - `__OUTPUT_PATH__` replaced at render time
4. **Exit codes** - 0=success, 1=SC error, 2=system error

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Output path resolution**
- **Found during:** Checkpoint verification
- **Issue:** Relative output paths failed because sclang's cwd is SC app directory
- **Fix:** Convert output path to absolute before passing to SC
- **Files modified:** src/audioloop/render.py
- **Verification:** JSON output test now passes with relative paths
- **Commit:** `2cf66af`

**2. [Rule 3 - Blocking] QT_QPA_PLATFORM environment variable**
- **Found during:** Task 3 execution
- **Issue:** macOS SC only has "cocoa" Qt plugin, not "offscreen"
- **Fix:** Only set QT_QPA_PLATFORM=offscreen on Linux
- **Files modified:** src/audioloop/sclang.py
- **Verification:** Renders work on macOS

**3. [Rule 3 - Blocking] SC var declaration syntax**
- **Found during:** Task 5/6 execution
- **Issue:** SC requires var declarations at block start, before expressions
- **Fix:** Moved var declarations to top of blocks in wrapper template
- **Files modified:** src/audioloop/wrapper.py, tests/fixtures/full_nrt.scd
- **Verification:** Both render modes produce valid WAV files

---

**Total deviations:** 3 auto-fixed (1 bug, 2 blocking)
**Impact on plan:** All fixes necessary for correct operation. No scope creep.

## Issues Encountered

None beyond the deviations listed above.

## Next Phase Readiness

- Render pipeline complete and tested
- Ready for Phase 2: Analysis Core (`audioloop analyze`)
- JSON output format established for Claude integration

---
*Phase: 01-render-pipeline*
*Completed: 2026-01-09*
