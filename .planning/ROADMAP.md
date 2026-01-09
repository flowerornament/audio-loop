# audio-loop Roadmap

## Milestone 1: Working Feedback Loop

The goal is a complete describe→render→analyze→listen→iterate workflow. After this milestone, you can describe sounds to Claude, have them rendered and analyzed, listen, provide feedback, and iterate.

---

### Phase 1: Render Pipeline - COMPLETE
**Goal:** Execute SuperCollider code and capture rendered audio
**Completed:** 2026-01-09 | [Summary](.planning/phases/01-render-pipeline/01-SUMMARY.md)

**Deliverables:**
- `audioloop` CLI entry point (Python/typer)
- `audioloop render <file.scd>` command with two modes:
  - Full NRT mode (for complex sounds with custom timing)
  - Simple function wrapping mode (for quick iteration with `--duration`)
- `__OUTPUT_PATH__` placeholder convention
- SC code execution via sclang subprocess (NRT mode)
- WAV file capture and validation
- Error handling for SC compilation/runtime failures
- JSON output for Claude parsing

**Technical Challenges:**
- sclang subprocess management (exit behavior, compilation errors)
- macOS path handling (sclang in app bundle)
- Headless operation (QT_QPA_PLATFORM=offscreen)

**Research:** Completed (see `.planning/phases/01-render-pipeline/RESEARCH.md`)

---

### Phase 2: Analysis Core - COMPLETE
**Goal:** Extract acoustic features Claude can reason about
**Completed:** 2026-01-09 | [Summary](.planning/phases/02-analysis-core/02-02-SUMMARY.md)

**Deliverables:**
- `audioloop analyze <file.wav>` command
- librosa-based feature extraction:
  - Spectral (per-channel L/R): centroid, rolloff, flatness, bandwidth
  - Temporal: RMS, crest factor, attack time
  - Stereo: width, L-R correlation, per-channel deltas
- Structured JSON output matching PROJECT.md schema
- Human-readable output with summary interpretation

**Not in this phase:**
- Psychoacoustic metrics (Milestone 2)
- Spectrogram visualization (Milestone 3)
- Temporal evolution features (beat tracking, pitch contours) - future

**Research:** Completed (see `.planning/phases/02-analysis-core/RESEARCH.md`)

---

### Phase 3: Iteration Tools - COMPLETE
**Goal:** Complete the loop with playback and comparison
**Completed:** 2026-01-09 | [Summary](.planning/phases/03-iteration-tools/03-02-SUMMARY.md)

**Deliverables:**
- `audioloop play <file.wav>` - system audio playback (afplay on macOS)
- `audioloop compare <a.wav> <b.wav>` - feature-by-feature delta analysis
- Comparison output optimized for Claude interpretation:
  - Direction indicators (up/down/unchanged)
  - Significance flags (>10% change)
  - Interpretive context ("darker/warmer", "snappier attack")
- Delta highlighting for iteration feedback

**Research:** Completed (see `.planning/phases/03-iteration-tools/RESEARCH.md`)

---

## Milestone 2: Psychoacoustics

Add perceptual metrics that better capture how sounds *feel*, not just their signal properties.

---

### Phase 4: Zwicker Model Integration
**Goal:** Psychoacoustic metrics via MoSQITo/Zwicker model

**Deliverables:**
- Roughness (asper) - perception of rapid amplitude modulation
- Sharpness (acum) - perception of high-frequency energy
- Fluctuation strength - perception of slow modulation
- LUFS loudness measurement
- Integration into `analyze` output

**Research:** Required - evaluate MoSQITo vs mosqito vs custom implementation

---

## Milestone 3: Advanced Features (TBD)

Scope to be defined after Milestones 1-2 are complete. Candidates:

- **Spectrogram visualization:** `--spectrogram out.png` for Claude's multimodal analysis
- **Descriptor discovery:** A/B workflow, experiment tracking, learned mappings
- **Reference comparison:** "Make it sound like [reference.wav]"
- **Temporal evolution:** Beat/tempo tracking, feature evolution over time

---

*Last updated: 2026-01-09*
