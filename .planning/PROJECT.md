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
| `audioloop analyze <file.wav>` | Acoustic analysis |
| `audioloop analyze <file.wav> --spectrogram out.png` | Include spectrogram image |
| `audioloop play <file.wav>` | Open in system audio player |
| `audioloop compare <a.wav> <b.wav>` | Side-by-side analysis (for A/B or reference comparison) |

All commands output JSON for Claude to parse. Human-readable format with `--human`.

### Analysis Output

Objective measurements that Claude interprets:

```json
{
  "file": "sound.wav",
  "duration_sec": 4.2,
  "sample_rate": 48000,
  "spectral": {
    "centroid_hz": 847,
    "rolloff_hz": 2100,
    "flatness": 0.12,
    "bandwidth_hz": 1200
  },
  "temporal": {
    "attack_ms": 48,
    "rms": 0.23,
    "crest_factor": 4.2
  },
  "psychoacoustic": {
    "roughness_asper": 0.23,
    "sharpness_acum": 0.8,
    "loudness_lufs": -14.2
  },
  "stereo": {
    "width": 0.72,
    "correlation": 0.85
  }
}
```

### Spectrogram

`--spectrogram out.png` generates an image Claude can read directly (multimodal). Claude can see harmonic structure, transients, frequency evolution - potentially more informative than numeric features alone.

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

v1 may not achieve full generality, but that's the direction. We start with what works and expand.

## Architecture Note: SC Process Management

The `audioloop render` command needs to:
- Manage the SuperCollider/sclang process
- Capture stdout for logging and error reporting
- Get rendered audio into the Python toolchain for analysis

This likely means a server or process manager sitting between the CLI and sclang. Multiple architectural approaches are possible - detailed design TBD in implementation planning.

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
| Sound synthesis | SuperCollider via sclang | Expressive, text-based, scriptable |
| Audio analysis | Python/librosa + MoSQITo | Feature extraction + psychoacoustics |
| CLI | Python/typer | Simple, good for JSON output |
| SC process management | TBD | Needs design work |

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

**Core Loop**
- [ ] `audioloop render` - SC process management, WAV capture, error reporting
- [ ] `audioloop analyze` - acoustic feature extraction
- [ ] `audioloop analyze --spectrogram` - spectrogram image generation
- [ ] `audioloop play` - system audio player
- [ ] `audioloop compare` - side-by-side analysis
- [ ] JSON output for all commands

## Out of Scope (v1)

- GUI or web interface
- Real-time synthesis
- Pre-built sound presets
- Cross-session vocabulary learning

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

---
*Last updated: 2026-01-09*
