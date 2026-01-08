# Phase 1 Research: Core Infrastructure

## Summary

Phase 1 involves building a Python CLI (`audioloop`) that executes SuperCollider code and captures rendered WAV files. The key challenges are:

1. **sclang subprocess management** - making sclang exit cleanly
2. **NRT vs RT rendering** - choosing the right approach
3. **macOS path handling** - sclang lives inside the app bundle

---

## SuperCollider Rendering Options

### Option A: Real-Time with Server Recording (NOT recommended)

Boot scsynth, play audio, record to disk. Problems:
- Requires audio hardware connection
- Subject to xruns (buffer underruns)
- Slower than NRT for offline rendering

### Option B: Non-Real-Time (NRT) Mode (RECOMMENDED)

Use `Score.recordNRT()` to render faster-than-realtime without audio hardware.

```supercollider
// Example: render a pattern to WAV
SynthDef(\pad, { |freq, dur|
    var sig = LPF.ar(Saw.ar(freq), 1000);
    var env = EnvGen.ar(Env.perc(0.1, dur), doneAction: 2);
    Out.ar(0, sig * env ! 2);
}).store;  // .store saves to disk for NRT

(
var score = Pbind(\instrument, \pad, \dur, 1, \degree, Pseq([0,2,4], 1)).asScore(4);
score.recordNRT(
    outputFilePath: "~/output.wav".standardizePath,
    headerFormat: "WAV",
    sampleFormat: "int24",
    options: ServerOptions.new.numOutputBusChannels_(2),
    duration: 5,
    action: { "Done".postln; 0.exit; }
);
)
```

**Key points:**
- Use `.store` not `.add` for SynthDefs (writes to disk for NRT access)
- `duration` parameter determines output length
- Must call `0.exit;` in action callback

Sources:
- [NRT Synthesis Guide](https://doc.sccode.org/Guides/Non-Realtime-Synthesis.html)
- [Mads Kjeldgaard NRT Tutorial](https://madskjeldgaard.dk/old-blog/2019-08-05-supercollider-how-to-render-patterns-as-sound-files-using-nrt/)

---

## sclang Exit Behavior (CRITICAL)

**Problem:** `sclang script.scd` hangs after execution instead of exiting.

**Solution:** Script must call `0.exit;` when done.

```supercollider
// At end of script:
0.exit;
```

**Caveat:** If there's a compilation error, sclang still hangs. Workaround: use subprocess timeout.

```python
import subprocess

result = subprocess.run(
    [sclang_path, script_path],
    capture_output=True,
    timeout=30,  # seconds
    text=True
)
```

For async rendering that needs to complete before exit:

```supercollider
fork {
    s.waitForBoot {
        // ... rendering code ...
    };
    // wait for render to complete
    score.recordNRT(
        // ...
        action: { 0.exit; }
    );
}
```

Sources:
- [GitHub Issue #3393](https://github.com/supercollider/supercollider/issues/3393)
- [Running sclang from Python](https://gewhere.github.io/running-sclang-from-python)

---

## macOS sclang Path

sclang is inside the app bundle, not in PATH:

```
/Applications/SuperCollider.app/Contents/MacOS/sclang
```

**Important:** Must `cd` into that directory before executing to avoid Qt/Cocoa issues:

```python
import subprocess
import os

SC_APP = "/Applications/SuperCollider.app"
SCLANG_DIR = f"{SC_APP}/Contents/MacOS"
SCLANG = f"{SCLANG_DIR}/sclang"

# Execute from sclang's directory
result = subprocess.run(
    [SCLANG, script_path],
    cwd=SCLANG_DIR,  # Critical!
    capture_output=True,
    timeout=60,
    text=True,
    env={**os.environ, "QT_QPA_PLATFORM": "offscreen"}
)
```

**Environment variable:** Set `QT_QPA_PLATFORM=offscreen` to avoid GUI initialization.

Sources:
- [SuperCollider macOS README](https://github.com/supercollider/supercollider/blob/develop/README_MACOS.md)

---

## Python CLI Framework: Typer

**Recommendation:** Use [Typer](https://typer.tiangolo.com/) over Click.

| Aspect | Typer | Click |
|--------|-------|-------|
| Boilerplate | Minimal | More verbose |
| Type hints | Native | Via decorators |
| Learning curve | Easy | Moderate |
| Built on | Click (compatible) | Native |

```python
import typer

app = typer.Typer()

@app.command()
def render(file: str, output: str = "output.wav"):
    """Render SuperCollider code to WAV."""
    typer.echo(f"Rendering {file} -> {output}")
    # ... subprocess call ...

if __name__ == "__main__":
    app()
```

Sources:
- [Typer Documentation](https://typer.tiangolo.com/)
- [Typer vs Click Comparison](https://johal.in/click-vs-typer-comparison-choosing-cli-frameworks-for-python-application-distribution/)

---

## Existing Python-SC Libraries

### sc3nb
Interactive sclang control for Jupyter. Overkill for our use case (we just need file rendering).

### sc3
Full SC3 reimplementation in Python. Wrong direction - we want to use actual SuperCollider.

**Recommendation:** Don't use these. Simple subprocess wrapper is cleaner for our needs.

---

## Recommended Architecture

```
audioloop render input.scd --output result.wav
    │
    ▼
┌─────────────────────────────────────────┐
│  1. Wrap user's SC code in NRT template │
│  2. Write to temp .scd file             │
│  3. Execute sclang subprocess           │
│  4. Timeout + error handling            │
│  5. Verify output WAV exists            │
│  6. Return path or error                │
└─────────────────────────────────────────┘
```

### NRT Wrapper Template

```supercollider
// Auto-generated wrapper
(
var outputPath = "__OUTPUT_PATH__";
var duration = __DURATION__;

// User's SynthDef(s) here - must use .store
__SYNTHDEF_CODE__

// User's synthesis code wrapped in Score
var score = Score([
    [0.0, [\d_recv, __SYNTHDEF_BYTES__]],
    __SCORE_EVENTS__
]);

score.recordNRT(
    outputFilePath: outputPath,
    headerFormat: "WAV",
    sampleFormat: "int24",
    options: ServerOptions.new.numOutputBusChannels_(2),
    duration: duration,
    action: { 0.exit; }
);
)
```

---

## What NOT to Hand-Roll

1. **Audio file I/O** - Use soundfile or scipy.io.wavfile
2. **CLI argument parsing** - Use Typer
3. **sclang process management** - Use subprocess with timeout (don't try to be clever)
4. **NRT synthesis** - Use SuperCollider's built-in Score.recordNRT

---

## Pitfalls to Avoid

1. **Don't forget `0.exit;`** - sclang will hang forever
2. **Don't skip `cwd` parameter** - sclang fails with Qt errors on macOS
3. **Don't use `.add` for SynthDefs** - NRT needs `.store` (disk-based)
4. **Don't skip timeout** - compilation errors cause infinite hang
5. **Don't parse sclang output for success** - check for output file existence instead
6. **Don't hardcode SC path** - make configurable, detect common locations

---

## Implementation Checklist

- [ ] Typer CLI skeleton with `render` command
- [ ] SC path detection (configurable, with fallback to `/Applications/SuperCollider.app`)
- [ ] Temp file management for .scd scripts
- [ ] subprocess.run with cwd, timeout, env vars
- [ ] Output file verification
- [ ] Error message extraction from sclang stdout/stderr
- [ ] Structured output (JSON) for Claude parsing
