# audio-loop

A toolkit for describing sounds to Claude Code and getting them out of SuperCollider.

## The Goal

You describe a sound in a Claude Code conversation:

> "a warm pad with slow attack, detuned oscillators, gentle filter movement"

Claude generates SuperCollider code, renders it, runs it through analysis, reviews the results, then you listen. If it's not right, you tell Claude what's off. Claude has both your feedback and the analysis data to inform adjustments. Iterate until it sounds how you want.

**The problem:** Claude can't hear. It generates code based on its understanding of synthesis, but has no way to verify whether the result actually sounds "warm" or has "gentle filter movement."

**The solution:** Give Claude detailed acoustic measurements of the rendered audio. Combined with your feedback ("not warm enough", "attack is too fast"), Claude can reason about the gap between what it produced and what you wanted.

## Example Session

A concrete example of the feedback loop:

```
You: "warm pad with slow attack"

Claude: writes SC code - filtered saw wave, 200ms attack,
        low-pass at 2kHz
        runs: audioloop render pad.scd
        runs: audioloop analyze pad.wav

Analysis shows: centroid 1847 Hz, attack 180ms

Claude: "Here's the first version. Centroid is around 1800 Hz,
        attack is 180ms. Give it a listen."

You: [listen] "Too bright, but the attack feels right"

Claude: sees centroid is high, your feedback confirms
        lowers filter cutoff from 2kHz to 800Hz
        re-renders, re-analyzes

Analysis shows: centroid 612 Hz, attack 180ms

Claude: "Brought the filter down. Centroid now at 612 Hz."

You: [listen] "That's it, that's warm"
```

The measurements help Claude understand *what* to change. Your ears determine *whether* it worked.

## How It Works

```
You describe a sound
        ↓
Claude writes SuperCollider code
        ↓
audioloop renders to WAV
        ↓
audioloop analyzes the audio
        ↓
Claude reviews analysis
        ↓
You listen and give feedback
        ↓
Claude has: your feedback + analysis data
        ↓
Claude adjusts code, re-renders
        ↓
Iterate until you're satisfied
```

**You are ground truth.** The analysis helps Claude understand what it produced. Your ears determine whether it matches what you asked for. Both inform Claude's next adjustment.

**Feedback is natural language.** You say "too bright" or "needs more punch" or "close but something's off." Claude interprets this against the analysis data to figure out what to adjust.

## Why SuperCollider

SuperCollider is expressive enough to synthesize almost anything - from simple sine waves to complex evolving textures. It's text-based (Claude can write it), scriptable (we can automate rendering), and has decades of sound design literature Claude can draw on.

The question isn't whether SC *can* make the sounds - it's whether Claude can learn to drive it effectively through iteration.

## The Core Bet

Acoustic measurements help Claude understand what it produced. Your feedback tells Claude whether it's right. Together, these let Claude make informed adjustments.

The adjustments might be small (tweak a filter cutoff) or large (try a completely different synthesis approach). "Warmer" might mean lowering a filter - or it might mean switching from FM to subtractive synthesis, or adding harmonics, or restructuring the entire signal chain.

Claude brings its knowledge of synthesis and psychoacoustics. The analysis gives Claude concrete data about what the sound actually is. Your ears are the final judge. Through iteration, Claude learns what works.

## When Things Go Wrong

**Syntax errors:** Claude sees the error message from sclang, fixes the code, tries again.

**Silence or garbage:** Analysis shows near-zero RMS or extreme values. Claude recognizes something went wrong structurally, not just parametrically.

**Not converging:** After several iterations, still not right. Options:
- You give more specific feedback ("the low end is fine, it's the mids that are harsh")
- Try a fundamentally different approach (different oscillator, different structure)
- Accept "close enough" or recognize this description needs more work

**Contradictory descriptions:** "Quiet but loud" - Claude asks for clarification or interprets creatively ("quiet spectrally but loud dynamically?").

The loop handles most failures naturally. Claude Code already knows how to debug, retry, and ask for help.

## When You're Done

Sound is good. What then?

The .scd and .wav files are in your repository. You might:
- Keep iterating on variations
- Move to a "finished" folder
- Use the SC code as a starting point for something else
- Come back later and refine

File organization conventions will emerge through use.

## The CLI Toolkit

Single entry point: `audioloop <command>`

| Command | Purpose |
|---------|---------|
| `audioloop render <file.scd>` | Execute SC code, capture WAV, return errors |
| `audioloop render <file.scd> --duration 4` | Render simple function syntax (auto-wrapped) |
| `audioloop analyze <file.wav>` | Acoustic analysis |
| `audioloop play <file.wav>` | Open in system audio player |
| `audioloop compare <a.wav> <b.wav>` | Side-by-side analysis (for A/B or reference comparison) |

All commands output JSON by default for Claude to parse. Human-readable format available.

### Analysis Output (v1)

Objective measurements that Claude interprets:

```json
{
  "file": "sound.wav",
  "duration_sec": 4.2,
  "sample_rate": 44100,
  "channels": 2,
  "spectral": {
    "left": {
      "centroid_hz": 847,
      "rolloff_hz": 2100,
      "flatness": 0.12,
      "bandwidth_hz": 1200
    },
    "right": {
      "centroid_hz": 892,
      "rolloff_hz": 2200,
      "flatness": 0.11,
      "bandwidth_hz": 1250
    }
  },
  "temporal": {
    "attack_ms": 48,
    "rms": 0.23,
    "crest_factor": 4.2
  },
  "stereo": {
    "width": 0.72,
    "correlation": 0.85
  }
}
```

*Note: Psychoacoustic metrics (roughness, sharpness, loudness) were added in v1.1 via MoSQITo/Zwicker model.*

### Spectrogram (Post-v1)

`--spectrogram out.png` will generate an image Claude can read directly (multimodal). Claude can see harmonic structure, transients, frequency evolution - potentially more informative than numeric features alone. This feature is planned for a future milestone.

### Error Handling

When SuperCollider code has errors, `render` captures stdout/stderr:

```json
{
  "success": false,
  "error": "ERROR: syntax error, unexpected BINOP\n  in file 'sound.scd'\n  line 12 char 5",
  "stdout": "..."
}
```

## Scope

**As general as possible.** The goal is arbitrary sound descriptions:

- "fuzzy sine wave"
- "warm pad with slow attack"
- "909 kick drum"
- "ambient texture with slow evolution"
- "make a techno track"

We start with what works and expand.

## v1 Scope

**v1 = Working Feedback Loop** (Milestone 1 in the roadmap)

v1 includes:
- `audioloop render` - with both full NRT and simple function wrapping
- `audioloop analyze` - spectral and temporal features (no psychoacoustics yet)
- `audioloop play` - system audio playback
- `audioloop compare` - side-by-side delta analysis

v1 does NOT include:
- Psychoacoustic metrics (roughness, sharpness, loudness) - Milestone 2
- Spectrogram visualization - Milestone 3
- Reference sound comparison - Milestone 3

## Architecture Note: SC Process Management

The `audioloop render` command uses SuperCollider's NRT (Non-Real-Time) mode for offline rendering. This avoids the complexity of managing a running audio server.

### Two Render Modes

**Full NRT Mode** - For complex sounds with custom timing:
```supercollider
// Full NRT code - user controls everything
SynthDef(\pad, { |out=0| ... }).store;
var score = Score([...]);
score.recordNRT(
    outputFilePath: "__OUTPUT_PATH__",  // <-- placeholder replaced by audioloop
    ...
    action: { 0.exit; }
);
```

**Simple Function Mode** - For quick iteration:
```supercollider
// Just the sound - audioloop wraps it in NRT boilerplate
{ LPF.ar(Saw.ar(200), 1000) * 0.3 ! 2 }
```
Render with: `audioloop render simple.scd --duration 4`

### Output Path Convention

Use the `__OUTPUT_PATH__` placeholder in your NRT code. `audioloop render` replaces it with the actual output path before execution. If the placeholder is missing in full NRT code, the render will likely fail (output goes to wrong location).

### Mode Detection

`audioloop render` checks for `recordNRT` in the file:
- **Found** → Full NRT mode (run as-is with placeholder replacement)
- **Not found** → Simple function mode (requires `--duration` flag)

## A/B Testing (Development Only)

During development, A/B testing validates the analysis toolkit:

1. Claude generates two sound variants
2. You listen and identify which better matches what you asked for
3. We see whether the analysis data correctly predicted your preference

This helps tune analysis parameters. It's not part of normal use - normal use is just the feedback loop (describe → render → listen → adjust).

## Analysis Features

| Category | Features | What They Measure |
|----------|----------|-------------------|
| Spectral | centroid, rolloff, flux, flatness, bandwidth | Frequency content, brightness, texture |
| Pitch | f0 tracking, harmonicity | Tuning, tonal quality |
| Amplitude | RMS, envelope, crest factor | Dynamics, attack/sustain |
| Temporal | onset strength, tempo | Rhythmic content |
| Stereo | mid/side ratio, L-R correlation | Width, imaging |
| Perceptual | loudness (LUFS), roughness, sharpness | Human hearing response |

**Why psychoacoustic metrics?** Roughness, sharpness, and loudness (via MoSQITo/Zwicker model) attempt to measure *perception*, not just signal properties. "Harsh" is better captured by roughness than by any single spectral feature.

## Technical Stack

| Component | Technology | Why |
|-----------|------------|-----|
| Sound synthesis | SuperCollider via sclang (NRT mode) | Expressive, text-based, scriptable, offline rendering |
| Audio analysis (v1) | Python/librosa | Feature extraction (spectral, temporal, stereo) |
| Audio analysis (post-v1) | + MoSQITo | Psychoacoustic metrics |
| CLI | Python/typer + rich | Simple, good for JSON output, nice formatting |

## Assumptions to Validate

- **Claude can write working SuperCollider code.** Likely true, and the error feedback loop helps it improve.
- **Acoustic measurements help Claude make better adjustments.** Core bet. Your feedback is ground truth; measurements help Claude understand what to change.
- **Spectrogram images provide useful information.** Claude is multimodal - does visual analysis actually help?
- **The feature-to-vocabulary mapping is learnable.** Can Claude reliably connect "warm" to centroid through iteration?

## Future Considerations

**Learning over time:** Within a conversation, Claude naturally learns your vocabulary. Cross-session learning would require explicit note-taking - Claude recording what interpretations worked for you.

**Reference sounds:** "Make it sound like this [reference.wav]" - Claude analyzes both reference and attempts, comparing features. Valuable when you have a specific target.

Not v1 scope, but worth considering if the core loop proves valuable.

## Requirements

### Validated (v2.0)
- [x] `audioloop iterate` - unified render→analyze→play workflow — v2.0
- [x] `audioloop analyze --spectrogram` - PNG spectrogram generation — v2.0
- [x] ASCII frequency band visualization in human output — v2.0
- [x] Unified CLI styling with semantic colors (layout.py) — v2.0
- [x] Real-world validation completed — v2.0

### Validated (v1.1)
- [x] Psychoacoustic metrics (loudness, sharpness, roughness via MoSQITo) — v1.1
- [x] `--no-psychoacoustic` flag for faster analysis — v1.1
- [x] Human-readable interpretation of psychoacoustic metrics — v1.1

### Validated (v1.0)
- [x] `audioloop render` - NRT rendering with both full and wrapped modes
- [x] `audioloop analyze` - spectral and temporal feature extraction
- [x] `audioloop play` - system audio player
- [x] `audioloop compare` - side-by-side delta analysis
- [x] JSON output for all commands

### Active (Future)
- [ ] Reference sound comparison (identified as powerful in v2.0 validation)

## Out of Scope

- GUI or web interface - CLI-first for Claude Code integration
- Real-time synthesis - NRT mode simplifies architecture
- Pre-built sound presets - Claude generates custom sounds
- Cross-session vocabulary learning - would require explicit note-taking

## Constraints

- SuperCollider installed and working
- macOS platform
- Python environment (librosa, MoSQITo, etc.)
- Claude Code CLI workflow

## Success Criteria

**Minimum viable:**
You say "warm pad with slow attack." Claude generates code, renders, analyzes, you listen, say "too bright," Claude sees the high centroid, adjusts the filter, re-renders, and the result actually sounds warm.

**Real success:**
You can describe sounds with varying complexity and Claude reliably produces something that matches - iterating as needed until you're satisfied.

**Stretch:**
Iteration usually converges in 1-3 attempts. Claude handles complex multi-element descriptions ("techno kick with sidechain pumping on a pad").

## Current State (v2.0)

- **Shipped:** 2026-01-11
- **LOC:** 2,607 Python
- **Tech stack:** Python/typer/rich, librosa, MoSQITo, matplotlib, SuperCollider (NRT mode)
- **Commands:** render, analyze, play, compare, iterate
- **Tests:** 80+ pytest tests
- **New in v2.0:** iterate command, spectrogram visualization, semantic CLI styling

**Validation insight:** The tool works as a diagnostic — it surfaces acoustic data that helps identify gaps between attempts and targets. Its value scales with the operator's production/sound-design knowledge.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Two render modes (full NRT + wrapped) | Full NRT for complex sounds, wrapped for quick iteration | Good |
| Mode detection via recordNRT presence | Simple, reliable detection | Good |
| __OUTPUT_PATH__ placeholder convention | Clean separation of SC code and output path | Good |
| Mean aggregation for spectral features | Single summary value simplifies Claude interpretation | Good |
| Reference ranges, not judgments | Context-dependent interpretation left to user/Claude | Good |
| >10% significance threshold | Filters noise, matches perceptual difference threshold | Good |
| Direct MoSQITo function API | Simpler than Audio class for single-file analysis | Good |
| Lazy import MoSQITo | Graceful fallback when not installed | Good |
| --no-psychoacoustic flag | Opt-out pattern clearer than opt-in | Good |
| Serial computation for MoSQITo | Parallelization overhead exceeded benefit (v2.0 profiling) | Good |
| JSON default for iterate command | Claude is primary user; direct parsing | Good |
| Stacked 3-subplot spectrogram | Waveform/mel/chroma with shared x-axis | Good |
| 6 frequency bands for ASCII | Matches audio engineering conventions | Good |
| Semantic style functions (layout.py) | Style by meaning not color; single source of truth | Good |

---
*Last updated: 2026-01-11 after v2.0 milestone*
