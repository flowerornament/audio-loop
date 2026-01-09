# Phase 1: Render Pipeline - Execution Plan

## Objective

Build the `audioloop render` command that executes SuperCollider code and captures rendered WAV files. This establishes the foundation for the describe→render→analyze→iterate workflow.

## Execution Context

**Dependencies:**
- Python 3.11+ (assumed available)
- SuperCollider 3.14.x installed at `/Applications/SuperCollider.app`
- No existing codebase - greenfield implementation

**Key Research Findings** (from RESEARCH.md):
- Use NRT (Non-Real-Time) mode via `Score.recordNRT()` for reliable offline rendering
- sclang requires explicit `0.exit;` to terminate (hangs otherwise)
- Must set `cwd` to SC MacOS directory and `QT_QPA_PLATFORM=offscreen`
- Compilation errors cause infinite hang - use timeout workaround (fixed in SC 3.15)
- Check stdout for ERROR patterns, not exit code
- Use Typer for CLI, Rich for human-readable output

**Constraints:**
- macOS only for now
- Focus on reliability over features

**Two Render Modes:**
- **Full NRT mode**: Claude writes complete NRT code with `__OUTPUT_PATH__` placeholder
- **Simple function mode**: Claude writes just `{ ... }` function, audioloop wraps it (requires `--duration`)

---

## Tasks

### Task 1: Project Setup
**Goal:** Initialize Python project structure with dependencies

**Actions:**
1. Create `pyproject.toml` with:
   - Package name: `audioloop`
   - Python requirement: `>=3.11`
   - Dependencies: `typer[all]>=0.9.0`, `rich>=13.0.0`
   - Dev dependencies: `pytest>=7.0.0`, `pytest-cov`
   - Entry point: `audioloop = "audioloop.cli:app"`
2. Create directory structure:
   ```
   src/audioloop/
       __init__.py
       cli.py
       render.py
   tests/
       __init__.py
       test_render.py
   ```
3. Create minimal `src/audioloop/__init__.py` with version
4. Run `pip install -e ".[dev]"` to install in development mode

**Verification:**
- `audioloop --help` shows available commands
- `python -c "import audioloop"` succeeds

---

### Task 2: SC Path Discovery
**Goal:** Locate and validate SuperCollider installation

**Actions:**
1. Create `src/audioloop/sc_paths.py` with:
   - `SC_APP_PATH` constant: `/Applications/SuperCollider.app`
   - `get_sclang_path()` function returning `{SC_APP}/Contents/MacOS/sclang`
   - `get_scsynth_path()` function returning `{SC_APP}/Contents/Resources/scsynth`
   - `validate_sc_installation()` that checks paths exist
   - Environment variable override: `AUDIOLOOP_SC_APP` to customize location
2. Add helpful error message if SC not found with installation instructions

**Verification:**
- `validate_sc_installation()` returns True on macOS with SC installed
- Override works: `AUDIOLOOP_SC_APP=/custom/path`

---

### Task 3: sclang Subprocess Execution
**Goal:** Execute sclang reliably with proper environment

**Actions:**
1. Create `src/audioloop/sclang.py` with:
   - `run_sclang(script_path: Path, timeout: float = 60.0) -> SclangResult`
   - `SclangResult` dataclass: `success: bool`, `stdout: str`, `stderr: str`, `exit_code: int`, `timed_out: bool`
   - Proper subprocess configuration:
     ```python
     subprocess.run(
         [sclang_path, str(script_path)],
         cwd=sclang_dir,  # CRITICAL for Qt/Cocoa
         capture_output=True,
         timeout=timeout,
         text=True,
         env={**os.environ, "QT_QPA_PLATFORM": "offscreen"}
     )
     ```
   - Timeout handling returning `timed_out=True` on TimeoutExpired
2. Handle common failure modes:
   - SC not installed → clear error message
   - Permission denied → suggest chmod fix
   - Timeout → indicate possible compilation error

**Verification:**
- Can execute simple SC script that prints and exits
- Timeout works for hanging scripts
- Returns clean result structure

---

### Task 4: Error Detection
**Goal:** Parse sclang output to detect errors reliably

**Actions:**
1. Create `src/audioloop/errors.py` with:
   - `SCError` dataclass: `message: str`, `file: str | None`, `line: int | None`, `char: int | None`
   - `has_error(output: str) -> bool` checking patterns:
     - `\bERROR\b`
     - `Library has not been compiled successfully`
     - `FAILURE IN SERVER`
   - `extract_error(output: str) -> SCError | None` parsing:
     ```
     ERROR: syntax error, unexpected BINOP
       in file '/path/to/file.scd'
       line 12 char 5
     ```
   - `format_error_human(error: SCError) -> str` for readable output

**Verification:**
- Test with sample error outputs from research
- Correctly extracts line/char from structured errors
- Handles errors without file/line info gracefully

---

### Task 5: NRT Wrapper Module
**Goal:** Generate NRT boilerplate for simple function syntax

**Actions:**
1. Create `src/audioloop/wrapper.py` with:
   - `needs_wrapping(code: str) -> bool` - returns True if `recordNRT` not found in code
   - `wrap_function(code: str, duration: float, output_path: Path) -> str` - generates full NRT script

2. NRT wrapper template:
   ```supercollider
   // Auto-generated NRT wrapper by audioloop
   (
   var userFunc = __USER_CODE__;
   var duration = __DURATION__;
   var outputPath = "__OUTPUT_PATH__";

   SynthDef(\audioloop_render, { |out=0|
       Out.ar(out, userFunc.value);
   }).store;

   var score = Score([
       [0.0, [\s_new, \audioloop_render, 1000, 0, 0]],
       [duration, [\n_free, 1000]],
   ]);

   score.recordNRT(
       outputFilePath: outputPath,
       headerFormat: "WAV",
       sampleFormat: "int24",
       options: ServerOptions.new.numOutputBusChannels_(2),
       duration: duration,
       action: { "Render complete".postln; 0.exit; }
   );
   )
   ```

3. `replace_placeholders(code: str, output_path: Path, duration: float | None) -> str`
   - Replace `__OUTPUT_PATH__` with actual path
   - Replace `__DURATION__` with duration value (for wrapped mode)
   - Replace `__USER_CODE__` with user's function (for wrapped mode)

**Verification:**
- `needs_wrapping("{ SinOsc.ar(440) }")` returns True
- `needs_wrapping("score.recordNRT(...)")` returns False
- `wrap_function` produces valid SC code
- Placeholders are correctly replaced

---

### Task 6: Render Command Implementation
**Goal:** `audioloop render <file.scd>` command with two modes

**Actions:**
1. Create `src/audioloop/render.py` with:
   - `RenderResult` dataclass:
     ```python
     @dataclass
     class RenderResult:
         success: bool
         output_path: Path | None
         duration_sec: float | None
         render_time_sec: float
         error: SCError | None
         sclang_output: str
         mode: str  # "full_nrt" or "wrapped"
     ```
   - `render(input_path: Path, output_path: Path, timeout: float, duration: float | None) -> RenderResult`:
     1. Validate input file exists
     2. Read file content
     3. Detect mode: `needs_wrapping(content)`
     4. If wrapped mode and duration is None → error
     5. Prepare script:
        - Full NRT: replace `__OUTPUT_PATH__` placeholder
        - Wrapped: generate full NRT from function
     6. Write prepared script to temp file
     7. Run sclang with timeout
     8. Check for errors in output
     9. Verify output file exists and has size > 0
     10. Get duration from output file
     11. Return structured result

2. Add to `src/audioloop/cli.py`:
   ```python
   @app.command()
   def render(
       file: Path = typer.Argument(..., help="SuperCollider file to render"),
       output: Path = typer.Option(None, "--output", "-o", help="Output WAV path"),
       duration: float = typer.Option(None, "--duration", "-d", help="Duration in seconds (required for simple function syntax)"),
       timeout: float = typer.Option(120.0, "--timeout", "-t", help="Timeout in seconds"),
       json_output: bool = typer.Option(False, "--json", "-j", help="Output JSON"),
   ):
   ```
   - Default output: same name as input with `.wav` extension
   - Error if simple function mode and `--duration` not provided
   - JSON output format matching PROJECT.md schema
   - Human output with Rich formatting (green success, red errors)

**Verification:**
- Renders full NRT script to WAV
- Renders simple function with `--duration` to WAV
- Returns error if simple function without `--duration`
- Returns structured error for invalid SC code
- JSON output is valid and parseable
- Human output is readable

---

### Checkpoint: Verify Render Output
**Type:** checkpoint:human-verify

**What was built:**
- Full `audioloop render` command with two modes:
  - Full NRT mode: `audioloop render full_nrt.scd`
  - Wrapped function mode: `audioloop render simple.scd --duration 2`
- Error detection and structured error output
- JSON output format for Claude parsing

**How to verify:**
1. Run: `audioloop render tests/fixtures/full_nrt.scd -o /tmp/test_full.wav`
2. Play the WAV: `afplay /tmp/test_full.wav` (should hear 1 second of 440Hz sine)
3. Run: `audioloop render tests/fixtures/simple_function.scd --duration 2 -o /tmp/test_simple.wav`
4. Play the WAV: `afplay /tmp/test_simple.wav` (should hear 2 seconds of filtered saw)
5. Check JSON output: `audioloop render tests/fixtures/full_nrt.scd --json`
6. Check error handling: `audioloop render tests/fixtures/syntax_error.scd`

**Resume signal:** Type "approved" if renders work and sound correct, or describe issues.

---

### Task 7: Test SC Scripts
**Goal:** Create test fixtures for validation

**Actions:**
1. Create `tests/fixtures/` directory

2. Create `tests/fixtures/full_nrt.scd` (full NRT mode test):
   ```supercollider
   // Full NRT render test - 1 second of 440Hz sine
   (
   SynthDef(\test, { |out=0|
       Out.ar(out, SinOsc.ar(440) * 0.3 ! 2);
   }).store;

   var score = Score([
       [0.0, [\s_new, \test, 1000, 0, 0]],
       [1.0, [\n_free, 1000]],
   ]);

   score.recordNRT(
       outputFilePath: "__OUTPUT_PATH__",
       headerFormat: "WAV",
       sampleFormat: "int24",
       options: ServerOptions.new.numOutputBusChannels_(2),
       duration: 1.0,
       action: { "Done".postln; 0.exit; }
   );
   )
   ```

3. Create `tests/fixtures/simple_function.scd` (wrapped mode test):
   ```supercollider
   // Simple function - will be wrapped by audioloop
   { LPF.ar(Saw.ar(200), 1000) * 0.3 ! 2 }
   ```

4. Create `tests/fixtures/syntax_error.scd`:
   ```supercollider
   // Intentional syntax error
   (
   var x = 1 +;  // error here
   )
   ```

5. Create `tests/fixtures/runtime_error.scd`:
   ```supercollider
   // Runtime error - undefined variable
   (
   unknownVariable.postln;
   0.exit;
   )
   ```

**Verification:**
- Files exist and have expected content
- full_nrt.scd produces valid WAV when placeholder is replaced
- simple_function.scd produces valid WAV when wrapped and rendered

---

### Task 8: Integration Tests
**Goal:** Test end-to-end render workflow for both modes

**Actions:**
1. Create `tests/test_render.py` with:
   - `test_render_full_nrt()` - renders full_nrt.scd, verifies WAV output
   - `test_render_wrapped_function()` - renders simple_function.scd with --duration, verifies WAV
   - `test_render_wrapped_without_duration()` - verifies error when --duration missing
   - `test_render_syntax_error()` - verifies error detection and structured error return
   - `test_render_missing_file()` - verifies clean error for nonexistent input
   - `test_render_timeout()` - verifies timeout handling
   - `test_render_output_path()` - verifies custom output path works
   - `test_json_output_format()` - verifies JSON matches expected schema

2. Create `tests/test_wrapper.py` with:
   - `test_needs_wrapping_true()` - simple function returns True
   - `test_needs_wrapping_false()` - full NRT returns False
   - `test_wrap_function_generates_valid_code()` - wrapped code contains NRT boilerplate
   - `test_placeholder_replacement()` - placeholders correctly replaced

3. Use pytest fixtures for temp directories and cleanup

4. Mark tests that require SC installation: `@pytest.mark.skipif(not sc_available())`

**Verification:**
- All tests pass
- Tests clean up temporary files
- Tests skip gracefully if SC not installed

---

### Task 9: CLI Polish
**Goal:** Finalize CLI user experience

**Actions:**
1. Add `--version` flag to CLI
2. Add helpful `--help` text for all commands
3. Ensure exit codes are correct:
   - 0 for success
   - 1 for SC errors (syntax, runtime)
   - 2 for system errors (SC not found, file not found, missing --duration)
4. Add `--verbose` flag to show sclang stdout
5. Test CLI manually:
   - `audioloop --version`
   - `audioloop render --help`
   - `audioloop render tests/fixtures/full_nrt.scd`
   - `audioloop render tests/fixtures/full_nrt.scd --json`
   - `audioloop render tests/fixtures/simple_function.scd --duration 2`
   - `audioloop render tests/fixtures/simple_function.scd` (should error: missing --duration)
   - `audioloop render tests/fixtures/syntax_error.scd`

**Verification:**
- All manual tests produce expected output
- Exit codes are correct
- Help text is clear and complete

---

## Verification Checklist

After all tasks complete:

- [ ] `audioloop --version` displays version
- [ ] `audioloop --help` shows render command
- [ ] `audioloop render full_nrt.scd` produces WAV file (full NRT mode)
- [ ] `audioloop render simple.scd --duration 4` produces WAV file (wrapped mode)
- [ ] `audioloop render simple.scd` shows "duration required" error
- [ ] `audioloop render valid.scd --json` outputs valid JSON with success=true
- [ ] `audioloop render invalid.scd` shows error message
- [ ] `audioloop render invalid.scd --json` outputs JSON with success=false and error details
- [ ] `audioloop render missing.scd` shows "file not found" error
- [ ] `pytest` passes all tests
- [ ] WAV files are valid (can be played by system audio player)

---

## Success Criteria

**Phase is complete when:**

1. `audioloop render` works in both full NRT and wrapped function modes
2. Mode detection correctly identifies which mode to use
3. `--duration` flag properly required for wrapped mode
4. Errors from SC are captured, parsed, and presented clearly
5. JSON output matches PROJECT.md schema for Claude parsing
6. Human-readable output is clear with Rich formatting
7. Tests provide confidence in core functionality
8. Code is clean, documented, and follows Python best practices

---

## Output

**Files created:**
- `pyproject.toml` - project configuration
- `src/audioloop/__init__.py` - package init
- `src/audioloop/cli.py` - CLI entry point
- `src/audioloop/sc_paths.py` - SC installation paths
- `src/audioloop/sclang.py` - subprocess execution
- `src/audioloop/errors.py` - error parsing
- `src/audioloop/wrapper.py` - NRT wrapping logic
- `src/audioloop/render.py` - render logic
- `tests/test_render.py` - render integration tests
- `tests/test_wrapper.py` - wrapper unit tests
- `tests/fixtures/*.scd` - test SC files

**Commands available:**
- `audioloop render <file.scd> [--output path.wav] [--duration N] [--timeout 120] [--json] [--verbose]`
- `audioloop --version`
- `audioloop --help`

---

## Notes

**Design Decisions:**
- Two render modes: full NRT (Claude writes everything) and wrapped (Claude writes just function)
- Mode detection: check for `recordNRT` in file content
- `__OUTPUT_PATH__` placeholder convention for output path injection
- `--duration` required for wrapped mode, ignored for full NRT
- Output path defaults to input filename with `.wav` extension
- Timeout defaults to 120s but should be adjusted for long renders

**Open Questions Resolved:**
- Template approach: Both minimal and wrapped supported
- Output path injection: String replacement with `__OUTPUT_PATH__` placeholder
- SC path: Check standard location, allow env var override, clear error if not found
- Timeout: User-configurable via `--timeout`, default 120s

**Future Considerations:**
- Pattern wrapping could be added as additional convenience
- Linux support would need different SC path detection

---

*Plan created: 2026-01-09*
*Updated: 2026-01-09 - Added wrapping mode support*
*Estimated scope: Medium (9 tasks, single session)*
