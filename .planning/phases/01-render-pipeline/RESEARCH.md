# Phase 1 Research: Core Infrastructure

## Summary

Phase 1 builds a Python CLI (`audioloop`) that executes SuperCollider code and captures rendered WAV files. The key technical challenges are:

1. **sclang subprocess management** - making sclang exit cleanly after rendering
2. **NRT (Non-Real-Time) rendering** - offline rendering without audio hardware
3. **macOS path handling** - sclang lives inside the app bundle
4. **Error detection** - parsing sclang output for compilation/runtime errors

---

## SuperCollider Version Status

**Current stable:** 3.14.1 (November 2024)

Key features relevant to this project:
- Qt6 migration (from Qt5)
- Themed documentation support
- `QT_QPA_PLATFORM=offscreen` confirmed working for headless mode

**Important:** PR #6727 (sclang exits on library compilation failure) was merged April 2025 into `develop` branch. This fix is NOT in 3.14.1 - we must still use timeout workarounds for compilation errors.

Sources:
- [SuperCollider Releases](https://github.com/supercollider/supercollider/releases)
- [PR #6727](https://github.com/supercollider/supercollider/pull/6727)

---

## Rendering Approach: NRT Mode (RECOMMENDED)

Use SuperCollider's Non-Real-Time (NRT) mode via `Score.recordNRT()` for offline rendering.

### Why NRT?

| Aspect | Real-Time | NRT |
|--------|-----------|-----|
| Audio hardware | Required | Not needed |
| Speed | 1x realtime | Faster than realtime |
| Reliability | Subject to xruns | Deterministic |
| Subprocess | Needs server boot | Single process |

### How NRT Works

1. You provide a Score (timestamped OSC messages)
2. scsynth processes the score as fast as possible
3. Output is written directly to file
4. No network connection, no interaction during render

### Basic NRT Template

```supercollider
(
// Define synth - must use .store for NRT
SynthDef(\pad, { |out=0, freq=440, dur=1|
    var sig = LPF.ar(Saw.ar(freq), 1000);
    var env = EnvGen.ar(Env.perc(0.1, dur), doneAction: 2);
    Out.ar(out, sig * env ! 2);
}).store;

// Convert pattern to Score
var score = Pbind(
    \instrument, \pad,
    \dur, 1,
    \degree, Pseq([0, 2, 4], 1)
).asScore(4);

// Render
score.recordNRT(
    outputFilePath: "~/output.wav".standardizePath,
    headerFormat: "WAV",
    sampleFormat: "int24",
    options: ServerOptions.new.numOutputBusChannels_(2),
    duration: 5,
    action: { "Done rendering".postln; 0.exit; }
);
)
```

### Critical NRT Gotchas

1. **Use `.store` not `.add`** - SynthDefs must be written to disk for NRT server to find them
2. **NRT server starts blank** - No SynthDefs, no Buffers carry over from sclang session
3. **Include SynthDefs in Score** - Either via `.store` (disk) or `\d_recv` message at time 0.0
4. **Use `timeOffset`** - When converting patterns, use `timeOffset: 0.001` to ensure SynthDef messages process before note events
5. **Async commands are sync in NRT** - Buffer loading, SynthDef receiving happen instantly (no need to wait)

### Alternative: Direct scsynth NRT

You can invoke scsynth directly with a pre-built OSC file:

```bash
scsynth -N score.osc _ output.wav 44100 WAV int24 -o 2
```

This bypasses sclang entirely but requires generating binary OSC files, which is complex. **Recommendation:** Use sclang + Score for simplicity.

Sources:
- [NRT Synthesis Guide (SC 3.14.0)](https://doc.sccode.org/Guides/Non-Realtime-Synthesis.html)
- [Score Class Documentation](https://doc.sccode.org/Classes/Score.html)
- [Mads Kjeldgaard NRT Tutorial](https://madskjeldgaard.dk/old-blog/2019-08-05-supercollider-how-to-render-patterns-as-sound-files-using-nrt/)

---

## sclang Exit Behavior (CRITICAL)

### The Problem

Running `sclang script.scd` hangs after execution instead of exiting. This happens because sclang enters an interactive command loop.

### Solution: Call `0.exit;`

Every script must explicitly exit:

```supercollider
// At end of script, or in NRT action callback:
0.exit;
```

### Compilation Errors Still Hang (in 3.14.x)

If there's a **compilation error**, sclang hangs even with `0.exit;` in the code (the code never runs).

**Workaround:** Use subprocess timeout.

```python
import subprocess

result = subprocess.run(
    [sclang_path, script_path],
    capture_output=True,
    timeout=60,  # seconds - adjust based on expected render time
    text=True
)
```

**Future fix:** SC 3.15+ will exit on compilation failure (PR #6727).

Sources:
- [GitHub Issue #3393](https://github.com/supercollider/supercollider/issues/3393)
- [GitHub Issue #5218](https://github.com/supercollider/supercollider/issues/5218)
- [Running sclang from Python](https://gewhere.github.io/running-sclang-from-python)

---

## macOS sclang Execution

### Path Location

sclang is inside the application bundle:

```
/Applications/SuperCollider.app/Contents/MacOS/sclang
/Applications/SuperCollider.app/Contents/Resources/scsynth
```

### Critical: Must Set Working Directory

Due to Cocoa/Qt framework loading, you **must** `cd` into the sclang directory or use `cwd` parameter:

```python
import subprocess
import os

SC_APP = "/Applications/SuperCollider.app"
SCLANG_DIR = f"{SC_APP}/Contents/MacOS"
SCLANG = f"{SCLANG_DIR}/sclang"

result = subprocess.run(
    [SCLANG, script_path],
    cwd=SCLANG_DIR,  # CRITICAL - prevents Qt/Cocoa errors
    capture_output=True,
    timeout=60,
    text=True,
    env={**os.environ, "QT_QPA_PLATFORM": "offscreen"}
)
```

### Headless Mode

Set `QT_QPA_PLATFORM=offscreen` to prevent GUI initialization:

```python
env={**os.environ, "QT_QPA_PLATFORM": "offscreen"}
```

This is confirmed working on macOS and Linux. Without it, sclang may fail with Qt platform plugin errors.

Sources:
- [SuperCollider macOS README](https://github.com/supercollider/supercollider/blob/main/README_MACOS.md)
- [GitHub Issue #5420](https://github.com/supercollider/supercollider/issues/5420)
- [supercollider.js Configuration](https://crucialfelix.gitbooks.io/supercollider-js-guide/content/lang/install-and-configuration.html)

---

## Error Detection

### Parsing sclang Output

sclang outputs errors to stdout (not stderr). Error format:

```
ERROR: syntax error, unexpected BINOP
  in file '/path/to/file.scd'
  line 12 char 5
```

### Detection Strategy

```python
import re

def has_error(output: str) -> bool:
    """Check if sclang output contains errors."""
    # Match ERROR or Library compilation failure
    error_patterns = [
        r'\bERROR\b',
        r'Library has not been compiled successfully',
        r'FAILURE IN SERVER',
    ]
    for pattern in error_patterns:
        if re.search(pattern, output, re.IGNORECASE):
            return True
    return False

def extract_error_details(output: str) -> dict | None:
    """Extract structured error info from sclang output."""
    match = re.search(
        r"ERROR: (.+?)\n\s+in file '([^']+)'\n\s+line (\d+) char (\d+)",
        output
    )
    if match:
        return {
            "message": match.group(1),
            "file": match.group(2),
            "line": int(match.group(3)),
            "char": int(match.group(4))
        }
    return None
```

### Don't Rely on Exit Code Alone

sclang may exit 0 even with errors. Always:
1. Check for ERROR patterns in stdout
2. Verify output file exists and has non-zero size
3. Use timeout to handle hanging

Sources:
- [Emacs sclang-interp.el](https://github.com/dathinaios/spacemacs-supercollider/blob/master/local/sclang/sclang-interp.el)
- [Running sclang from Python](https://gewhere.github.io/running-sclang-from-python)

---

## Python CLI Framework: Typer

**Recommendation:** Use [Typer](https://typer.tiangolo.com/) for CLI.

### Why Typer?

- Minimal boilerplate via type hints
- Built on Click (battle-tested)
- Native Rich integration for formatted output
- Easy JSON output support

### Basic Structure

```python
import typer
from rich.console import Console
import json

app = typer.Typer()
console = Console()

@app.command()
def render(
    file: str,
    output: str = "output.wav",
    json_output: bool = typer.Option(False, "--json", "-j", help="Output JSON")
):
    """Render SuperCollider code to WAV."""
    result = do_render(file, output)

    if json_output:
        print(json.dumps(result, indent=2))
    else:
        if result["success"]:
            console.print(f"[green]Rendered:[/green] {result['output']}")
        else:
            console.print(f"[red]Error:[/red] {result['error']}")

if __name__ == "__main__":
    app()
```

### JSON Output Convention

All commands should support `--json` flag with consistent structure:

```json
{
  "success": true,
  "output": "/path/to/output.wav",
  "duration_sec": 5.0,
  "render_time_sec": 0.8
}
```

Or on error:

```json
{
  "success": false,
  "error": "syntax error, unexpected BINOP",
  "error_detail": {
    "file": "input.scd",
    "line": 12,
    "char": 5
  }
}
```

Sources:
- [Typer Documentation](https://typer.tiangolo.com/)
- [Building Modern CLI with Typer and Rich](https://www.codecentric.de/en/knowledge-hub/blog/lets-build-a-modern-cmd-tool-with-python-using-typer-and-rich)

---

## Existing Python-SC Libraries

### sc3nb

Interactive sclang control for Jupyter notebooks. Has NRT support via `Score.record_nrt()`.

**Evaluation:** Designed for interactive/Jupyter use. Overkill for our simple file-based workflow. Adds complexity without benefit.

### sc3

Full SC3 reimplementation in Python. Write sclang-style code in Python.

**Evaluation:** Wrong direction - we want Claude to write actual SuperCollider code, not Python-SC.

**Recommendation:** Don't use either. Simple subprocess wrapper gives us exactly what we need with full control.

Sources:
- [sc3nb GitHub](https://github.com/interactive-sonification/sc3nb)
- [sc3 GitHub](https://github.com/smrg-lm/sc3)

---

## Recommended Architecture

```
audioloop render input.scd --output result.wav
    │
    ▼
┌─────────────────────────────────────────┐
│  1. Validate input file exists          │
│  2. Wrap SC code in NRT template        │
│  3. Write to temp .scd file             │
│  4. Execute sclang subprocess           │
│     - cwd = SC MacOS directory          │
│     - env = QT_QPA_PLATFORM=offscreen   │
│     - timeout = duration + buffer       │
│  5. Parse stdout for errors             │
│  6. Verify output WAV exists + size > 0 │
│  7. Return JSON result or error         │
└─────────────────────────────────────────┘
```

### NRT Wrapper Template

The render command wraps user code in an NRT-compatible template:

```supercollider
// Auto-generated NRT wrapper
(
var outputPath = "__OUTPUT_PATH__";
var duration = __DURATION__;

// ===== USER CODE START =====
__USER_CODE__
// ===== USER CODE END =====

// Find the score variable or create from last expression
var score = __SCORE_VAR__;

score.sort;
score.recordNRT(
    outputFilePath: outputPath,
    headerFormat: "WAV",
    sampleFormat: "int24",
    options: ServerOptions.new.numOutputBusChannels_(2),
    duration: duration,
    action: { "NRT render complete".postln; 0.exit; }
);
)
```

**Design question:** How much wrapping vs. expecting user to write NRT-compatible code? Options:
1. **Minimal wrapping** - User writes full NRT code, we just ensure `0.exit;`
2. **Pattern wrapping** - User writes Pbind, we wrap in `.asScore.recordNRT`
3. **Full wrapping** - User writes SynthDefs + play code, we transform to NRT

Recommendation: Start with **option 1** (minimal wrapping). Let Claude write proper NRT code. Add convenience wrappers if patterns emerge.

---

## What NOT to Hand-Roll

1. **Audio file I/O** - Use `soundfile` or `scipy.io.wavfile`
2. **CLI argument parsing** - Use Typer
3. **JSON serialization** - Use stdlib `json`
4. **NRT synthesis** - Use SC's built-in Score.recordNRT
5. **OSC binary format** - If needed, use `python-osc`, don't hand-roll

---

## Pitfalls to Avoid

1. **Don't forget `0.exit;`** - sclang hangs forever without it
2. **Don't skip `cwd` parameter** - sclang fails with Qt errors on macOS
3. **Don't use `.add` for SynthDefs in NRT** - Use `.store` (writes to disk)
4. **Don't skip timeout** - compilation errors cause infinite hang (until SC 3.15)
5. **Don't parse exit code for success** - Check stdout AND output file existence
6. **Don't hardcode SC path** - Make configurable, detect common locations
7. **Don't assume stderr for errors** - sclang writes errors to stdout
8. **Don't forget QT_QPA_PLATFORM** - Required for headless operation

---

## Implementation Checklist

- [ ] Typer CLI skeleton with `render` command
- [ ] SC path detection (configurable via env var, fallback to common locations)
- [ ] Temp file management for wrapped .scd scripts
- [ ] subprocess.run with:
  - [ ] cwd set to SC MacOS directory
  - [ ] QT_QPA_PLATFORM=offscreen in env
  - [ ] timeout based on expected duration + buffer
  - [ ] capture_output=True, text=True
- [ ] Error detection (parse stdout for ERROR patterns)
- [ ] Output file verification (exists, size > 0)
- [ ] Structured JSON output for Claude parsing
- [ ] Human-readable output with Rich formatting
- [ ] `--json` flag on all commands

---

## Open Questions

1. **Template approach:** How much NRT boilerplate should audioloop inject vs. expecting Claude to write?
2. **Duration parameter:** Should user specify duration, or should we detect from score?
3. **SC path discovery:** Hard-code common locations or require configuration?
4. **Timeout calculation:** Fixed timeout or based on specified duration?

---

*Last updated: 2025-01-09*
*SuperCollider version: 3.14.1*
