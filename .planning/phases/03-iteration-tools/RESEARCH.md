# Phase 3: Feedback Loop - Research

## Executive Summary

Phase 3 completes the iteration toolkit with two commands:

- **`audioloop compare <a.wav> <b.wav>`** - Side-by-side feature comparison with deltas
- **`audioloop play <file.wav>`** - System audio playback

The feedback loop itself is simple: Claude calls tools, reads analysis, interprets your natural language feedback, and adjusts. No formal verification system needed - the user's ears are ground truth.

**Key findings:**
- **Comparison**: Reuse Phase 2's analysis pipeline, compute feature deltas, highlight significant changes
- **Playback**: Direct subprocess (`afplay` on macOS) is simpler and more reliable than library dependencies
- **Output design**: Optimize for Claude interpretation - direction indicators, significance flags, interpretive context

---

## 1. Audio Comparison Design

### Philosophy

The compare command helps Claude understand what changed between iterations. It's not about "similarity scores" - it's about **specific, interpretable deltas** that Claude can reason about.

Example scenario:
```
Iteration 1: centroid 1847 Hz (too bright)
Iteration 2: centroid 823 Hz

Delta: -1024 Hz (significant decrease)
Interpretation: "Filter lowered significantly"
```

Claude sees the delta, knows the direction was right, can decide if adjustment was enough.

### Implementation: Reuse Phase 2

The compare command runs Phase 2's analyze twice and computes differences:

```python
from audioloop.analyze import analyze_audio

def compare_audio(file_a: str, file_b: str) -> dict:
    """Compare two audio files feature-by-feature."""
    analysis_a = analyze_audio(file_a)
    analysis_b = analyze_audio(file_b)

    return compute_deltas(analysis_a, analysis_b)
```

**Don't add new analysis libraries.** Feature-by-feature comparison using existing analysis is exactly what's needed.

### Delta Computation

```python
from dataclasses import dataclass
from typing import Literal

@dataclass
class FeatureDelta:
    metric: str
    value_a: float
    value_b: float
    delta: float
    percent_change: float | None
    direction: Literal['up', 'down', 'unchanged']
    significant: bool  # > 10% change
    unit: str

def compute_deltas(analysis_a: dict, analysis_b: dict) -> dict:
    """Compute feature deltas between two analyses."""
    deltas = {}

    # Flatten nested dicts and compare
    flat_a = flatten_analysis(analysis_a)
    flat_b = flatten_analysis(analysis_b)

    for key in flat_a:
        if key in flat_b and isinstance(flat_a[key], (int, float)):
            val_a = flat_a[key]
            val_b = flat_b[key]
            delta = val_b - val_a

            # Percent change (handle zero)
            if abs(val_a) > 1e-10:
                pct = (delta / val_a) * 100
            else:
                pct = None

            # Direction
            if abs(delta) < 1e-10:
                direction = 'unchanged'
            else:
                direction = 'up' if delta > 0 else 'down'

            # Significance (>10% change)
            significant = pct is not None and abs(pct) > 10

            deltas[key] = FeatureDelta(
                metric=key,
                value_a=val_a,
                value_b=val_b,
                delta=delta,
                percent_change=pct,
                direction=direction,
                significant=significant,
                unit=get_unit(key),
            )

    return deltas
```

### Significance Thresholds

Not all changes matter. Define thresholds for "significant" changes:

| Metric | Threshold | Rationale |
|--------|-----------|-----------|
| centroid_hz | > 100 Hz | Audible brightness difference |
| attack_ms | > 10 ms | Perceivable envelope change |
| loudness_lufs | > 1 dB | Audible level difference |
| stereo_width | > 0.1 | Noticeable imaging change |
| roughness_asper | > 0.05 | Perceivable texture change |
| tempo_bpm | > 2 BPM | Noticeable rhythm shift |

These can be tuned based on experience.

### Output Format: Human-Readable

```
audioloop compare iter-1.wav iter-2.wav

Comparison: iter-1.wav -> iter-2.wav
Duration: 4.2s -> 4.2s (unchanged)

SPECTRAL (significant changes)
  centroid:     1847 Hz -> 823 Hz   (-1024 Hz, -55%)
  rolloff:      4200 Hz -> 2100 Hz  (-2100 Hz, -50%)

DYNAMICS (no significant changes)
  attack:       52 ms -> 55 ms      (+3 ms)
  rms:          0.23 -> 0.24        (+0.01)

PSYCHOACOUSTIC
  roughness:    0.15 -> 0.18        (+0.03 asper)
  loudness:     -16.2 -> -14.8 LUFS (+1.4 dB) *louder*

Summary: Significant spectral changes (darker/warmer).
         Dynamics similar. Slightly louder.
```

### Output Format: JSON (for Claude)

```json
{
  "file_a": "iter-1.wav",
  "file_b": "iter-2.wav",
  "summary": {
    "significant_changes": ["centroid", "rolloff"],
    "direction": "darker/warmer",
    "dynamics_changed": false
  },
  "deltas": {
    "spectral": {
      "centroid_hz": {
        "a": 1847,
        "b": 823,
        "delta": -1024,
        "percent": -55.4,
        "direction": "down",
        "significant": true,
        "interpretation": "significantly darker"
      },
      "rolloff_hz": {
        "a": 4200,
        "b": 2100,
        "delta": -2100,
        "percent": -50.0,
        "direction": "down",
        "significant": true
      }
    },
    "dynamics": {
      "attack_ms": {
        "a": 52,
        "b": 55,
        "delta": 3,
        "percent": 5.8,
        "direction": "up",
        "significant": false
      }
    },
    "psychoacoustic": {
      "loudness_lufs": {
        "a": -16.2,
        "b": -14.8,
        "delta": 1.4,
        "direction": "up",
        "significant": true,
        "interpretation": "noticeably louder"
      }
    }
  }
}
```

### Interpretation Layer

Add interpretive text for significant changes:

```python
INTERPRETATIONS = {
    'centroid_hz': {
        'down': 'darker/warmer',
        'up': 'brighter/harsher',
    },
    'attack_ms': {
        'down': 'snappier attack',
        'up': 'slower/softer attack',
    },
    'loudness_lufs': {
        'down': 'quieter',
        'up': 'louder',
    },
    'stereo_width': {
        'down': 'narrower',
        'up': 'wider',
    },
    'roughness_asper': {
        'down': 'smoother',
        'up': 'rougher/grittier',
    },
}

def interpret_delta(metric: str, direction: str) -> str | None:
    """Get interpretive text for a delta."""
    if metric in INTERPRETATIONS:
        return INTERPRETATIONS[metric].get(direction)
    return None
```

---

## 2. Audio Playback Design

### Approach: Direct Subprocess

For CLI audio playback, direct subprocess is simpler and more reliable than library dependencies:

**Pros:**
- Zero additional dependencies
- Uses system's native audio stack
- Works reliably on each platform
- User can interrupt with Ctrl+C

**Cons:**
- Less control (can't pause/stop programmatically)
- Platform-specific code paths

For our use case (play a file, user listens, gives feedback), subprocess is perfect.

### Implementation

```python
import platform
import subprocess
import shutil
from pathlib import Path

def play_audio(file_path: str, blocking: bool = True) -> subprocess.Popen | None:
    """Play audio file using system player.

    Args:
        file_path: Path to audio file
        blocking: If True, wait for playback to complete

    Returns:
        Popen object if non-blocking, None if blocking

    Raises:
        FileNotFoundError: If audio file doesn't exist
        RuntimeError: If no suitable player found
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    system = platform.system()

    if system == "Darwin":  # macOS
        cmd = ["afplay", str(path)]
    elif system == "Linux":
        # Try players in preference order
        players = [
            ("paplay", []),      # PulseAudio (most common)
            ("aplay", ["-q"]),   # ALSA
            ("ffplay", ["-nodisp", "-autoexit"]),  # FFmpeg
        ]
        cmd = None
        for player, args in players:
            if shutil.which(player):
                cmd = [player] + args + [str(path)]
                break
        if cmd is None:
            raise RuntimeError(
                "No audio player found. Install pulseaudio-utils, alsa-utils, or ffmpeg."
            )
    elif system == "Windows":
        # PowerShell Media.SoundPlayer (WAV only) or ffplay
        if path.suffix.lower() == ".wav":
            cmd = [
                "powershell", "-c",
                f"(New-Object Media.SoundPlayer '{path}').PlaySync()"
            ]
        elif shutil.which("ffplay"):
            cmd = ["ffplay", "-nodisp", "-autoexit", str(path)]
        else:
            raise RuntimeError(
                "Windows WAV playback requires PowerShell. "
                "For other formats, install ffmpeg."
            )
    else:
        raise RuntimeError(f"Unsupported platform: {system}")

    if blocking:
        subprocess.run(cmd, check=True)
        return None
    else:
        return subprocess.Popen(cmd)
```

### macOS `afplay` Details

`afplay` is the recommended player on macOS:

| Feature | Value |
|---------|-------|
| Location | `/usr/bin/afplay` (built-in) |
| Formats | WAV, AIFF, MP3, M4A, FLAC, etc. |
| Behavior | Blocks until complete |
| Exit codes | 0 = success, non-zero = error |
| Options | `-v volume`, `-t seconds` (stop after), `-q` (quiet) |

Useful options:
```bash
afplay -v 0.5 file.wav   # Play at 50% volume
afplay -t 5 file.wav     # Stop after 5 seconds
```

### Linux Player Fallback Chain

Linux audio is fragmented. Try players in this order:

1. **paplay** (PulseAudio) - Most modern distros
2. **aplay** (ALSA) - Lower-level, always available
3. **ffplay** (FFmpeg) - Universal fallback

```python
LINUX_PLAYERS = [
    ("paplay", [], "PulseAudio"),
    ("pw-play", [], "PipeWire"),  # Newer, gaining adoption
    ("aplay", ["-q"], "ALSA"),
    ("ffplay", ["-nodisp", "-autoexit", "-loglevel", "error"], "FFmpeg"),
]
```

### Alternative: playsound3 Library

If cross-platform consistency becomes important, [playsound3](https://github.com/szmikler/playsound3) is a viable option:

```python
from playsound3 import playsound

# Blocking (default)
playsound("/path/to/sound.wav")

# Non-blocking
sound = playsound("/path/to/sound.wav", block=False)
if sound.is_alive():
    print("Still playing...")
sound.stop()  # Stop early if needed
```

**Pros:**
- Single API for all platforms
- Non-blocking with stop support
- URL playback support

**Cons:**
- Extra dependency
- Another layer between us and the OS

**Recommendation:** Start with direct subprocess. Consider playsound3 if users report playback issues.

---

## 3. CLI Integration

### Command Structure

```python
import typer
from rich.console import Console
import json

app = typer.Typer()
console = Console()

@app.command()
def compare(
    file_a: str = typer.Argument(..., help="First audio file"),
    file_b: str = typer.Argument(..., help="Second audio file"),
    json_output: bool = typer.Option(False, "--json", "-j", help="JSON output"),
):
    """Compare two audio files and show feature deltas."""
    result = compare_audio(file_a, file_b)

    if json_output:
        print(json.dumps(result, indent=2))
    else:
        display_comparison(result)

@app.command()
def play(
    file: str = typer.Argument(..., help="Audio file to play"),
):
    """Play audio file using system player."""
    try:
        play_audio(file)
        console.print(f"[dim]Played: {file}[/dim]")
    except FileNotFoundError:
        console.print(f"[red]Error: File not found: {file}[/red]")
        raise typer.Exit(1)
    except RuntimeError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
```

### Return Values

For JSON output consistency:

```python
# audioloop compare --json
{
  "success": true,
  "file_a": "iter-1.wav",
  "file_b": "iter-2.wav",
  "deltas": { ... }
}

# audioloop play (no JSON - just plays)
# Exit code 0 = success, 1 = error
```

---

## 4. What NOT to Build

| Don't Build | Use Instead | Why |
|-------------|-------------|-----|
| Audio similarity scores | Feature deltas | Claude needs specifics, not aggregates |
| Custom comparison metrics | Phase 2 analysis twice | Already have the features |
| Cross-platform audio library | Direct subprocess | Simpler, fewer deps, more reliable |
| Playback progress bar | Simple blocking play | User just needs to listen |

---

## 5. Common Pitfalls

| Pitfall | Solution |
|---------|----------|
| Comparing files with different sample rates | Normalize in Phase 2 analysis |
| Comparing files with different durations | Show duration delta, warn if >10% different |
| afplay hangs on missing file | Check file exists before subprocess |
| Linux no audio output | Clear error message about which player to install |
| Windows WAV-only limitation | Recommend ffmpeg for other formats |
| Percent change on zero values | Handle division by zero, show "N/A" |

---

## 6. Dependencies

```toml
[project.dependencies]
# From Phase 1 & 2 (already installed)
# typer, rich, librosa, etc.

# No new dependencies for Phase 3!
# compare: reuses Phase 2 analysis
# play: uses system subprocess
```

Optional (only if subprocess approach fails):
```toml
[project.optional-dependencies]
audio = [
    "playsound3>=2.3.0",  # Cross-platform audio playback
]
```

---

## 7. Architecture

```
audioloop compare <a.wav> <b.wav>
         │
         ▼
┌─────────────────────────────────────┐
│  Run Phase 2 Analysis (twice)        │
│  - analyze(a.wav) -> features_a     │
│  - analyze(b.wav) -> features_b     │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Compute Deltas                      │
│  - For each feature: b - a          │
│  - Calculate percent change         │
│  - Determine direction (up/down)    │
│  - Flag significant changes (>10%)  │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Add Interpretation                  │
│  - "darker/warmer" for centroid↓   │
│  - "snappier" for attack↓          │
│  - Summary of overall change        │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Output                              │
│  - JSON (--json) for Claude         │
│  - Rich table for humans            │
└─────────────────────────────────────┘


audioloop play <file.wav>
         │
         ▼
┌─────────────────────────────────────┐
│  Validate File Exists                │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  Detect Platform                     │
│  - Darwin -> afplay                 │
│  - Linux -> paplay/aplay/ffplay     │
│  - Windows -> PowerShell/ffplay     │
└─────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  subprocess.run()                    │
│  - Block until playback complete    │
│  - User listens and provides        │
│    natural language feedback        │
└─────────────────────────────────────┘
```

---

## Sources

### Audio Playback
- [playsound3 PyPI](https://pypi.org/project/playsound3/) - Cross-platform audio playback library
- [playsound3 GitHub](https://github.com/szmikler/playsound3) - Source and documentation
- [boombox GitHub](https://github.com/mixmastamyk/boombox) - Alternative cross-platform player
- [Playing and Recording Sound in Python](https://realpython.com/playing-and-recording-sound-python/) - Overview of Python audio libraries

### Audio Analysis/Comparison
- [librosa GitHub](https://github.com/librosa/librosa) - Audio analysis library
- [librosa Tutorial](https://librosa.org/doc/main/tutorial.html) - Feature extraction guide
- [librosa Delta Features](https://librosa.org/doc/main/generated/librosa.feature.delta.html) - Computing feature derivatives

### Platform-Specific
- macOS afplay: Built-in, run `man afplay` for options
- Linux audio: [ALSA aplay](https://linux.die.net/man/1/aplay), [PulseAudio paplay](https://linux.die.net/man/1/paplay)

---

*Research completed: 2026-01-09*
*Simplified from original (removed EXPECT/sessions/verification)*
