# Project Milestones: audio-loop

## v2.0 Analysis Upgrades (Shipped: 2026-01-11)

**Delivered:** Faster iteration workflow with `iterate` command, spectrogram visualization, and real-world validation proving the tool works as a diagnostic

**Phases completed:** 5-7 (4 plans + 1 validation session)

**Key accomplishments:**
- `audioloop iterate` command — single invocation for render→analyze→play workflow
- Performance profiling identified MoSQITo loudness as bottleneck; sub-5s for 1-4s audio
- Spectrogram PNG generation (waveform/mel-spectrogram/chromagram stacked)
- ASCII frequency band visualization in terminal output
- Unified CLI styling with semantic color system (layout.py)
- Real-world validation: "Tool is diagnostic, not prescription" insight

**Stats:**
- 492 lines added (2,607 total Python)
- 5 phases (including 2 inserted decimal phases), 4 plans
- 3 days (2026-01-09 → 2026-01-11)

**Git range:** `b57532d` (docs: create milestone v2.0) → `0283fba` (docs(07): capture phase context)

**Key insight from validation:** The tool delivers objective acoustic data. Its value scales with the production/sound-design knowledge of the operator. Reference comparison workflow identified as particularly powerful.

**What's next:** TBD — discuss next milestone

---

## v1.1 Psychoacoustics (Shipped: 2026-01-09)

**Delivered:** Perceptual audio metrics via MoSQITo/Zwicker model for loudness, sharpness, and roughness

**Phases completed:** 4 (2 plans total)

**Key accomplishments:**
- Zwicker loudness (sones) via MoSQITo library integration
- Sharpness (acum) for high-frequency energy perception
- Roughness (asper) for amplitude modulation perception
- Graceful fallback when MoSQITo unavailable (optional dependency)
- `--no-psychoacoustic` flag for faster analysis
- Human-readable interpretation with perceptual labels

**Stats:**
- 4 files created/modified in src/
- 218 lines added (2,115 total Python)
- 1 phase, 2 plans
- Same day (2026-01-09)

**Git range:** `feat(04-01)` → `feat(04-02)`

**What's next:** v2.0 Advanced Features - spectrogram visualization, descriptor discovery, reference comparison

---

## v1.0 Working Feedback Loop (Shipped: 2026-01-09)

**Delivered:** Complete describe-render-analyze-listen-iterate workflow for AI-assisted sound design with SuperCollider

**Phases completed:** 1-3 (5 plans total)

**Key accomplishments:**
- `audioloop render` with dual modes (full NRT + wrapped function) for SuperCollider synthesis
- `audioloop analyze` with librosa-based spectral/temporal/stereo feature extraction
- `audioloop play` for system audio playback via afplay
- `audioloop compare` for feature-by-feature delta analysis with interpretation layer
- JSON output for Claude integration across all commands
- Comprehensive test suite (39+ tests)

**Stats:**
- 44 files created/modified
- 1,868 lines of Python
- 3 phases, 5 plans
- 2 days from start to ship (2026-01-07 → 2026-01-09)

**Git range:** `feat(01-01)` → `feat(03-02)`

**What's next:** v1.1 Psychoacoustics - Zwicker model integration for roughness, sharpness, and LUFS

---
