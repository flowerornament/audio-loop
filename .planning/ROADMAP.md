# audio-loop Roadmap

## Milestones

- [v1.0 Working Feedback Loop](milestones/v1.0-ROADMAP.md) (Phases 1-3) SHIPPED 2026-01-09
- **v1.1 Psychoacoustics** Phases 4+ (planned)
- v2.0 Advanced Features (TBD)

## Completed Milestones

<details>
<summary>v1.0 Working Feedback Loop (Phases 1-3) SHIPPED 2026-01-09</summary>

- [x] Phase 1: Render Pipeline (1/1 plans) completed 2026-01-09
- [x] Phase 2: Analysis Core (2/2 plans) completed 2026-01-09
- [x] Phase 3: Iteration Tools (2/2 plans) completed 2026-01-09

**Delivered:** Complete describe-render-analyze-listen-iterate workflow

[Full details](milestones/v1.0-ROADMAP.md)

</details>

---

## v1.1 Psychoacoustics (Complete)

Add perceptual metrics that better capture how sounds *feel*, not just their signal properties.

---

### Phase 4: Zwicker Model Integration - COMPLETE (2026-01-09)
**Goal:** Psychoacoustic metrics via MoSQITo/Zwicker model

**Delivered:**
- Loudness (sones) - Zwicker loudness via MoSQITo
- Sharpness (acum) - perception of high-frequency energy
- Roughness (asper) - perception of rapid amplitude modulation
- Integration into `analyze` output with graceful fallback

**Note:** Fluctuation strength skipped (not implemented in MoSQITo). LUFS was already present from Phase 2.

---

## v2.0 Advanced Features (TBD)

Scope to be defined after v1.1 is complete. Candidates:

- **Spectrogram visualization:** `--spectrogram out.png` for Claude's multimodal analysis
- **Descriptor discovery:** A/B workflow, experiment tracking, learned mappings
- **Reference comparison:** "Make it sound like [reference.wav]"
- **Temporal evolution:** Beat/tempo tracking, feature evolution over time

---

## Progress

| Phase | Milestone | Plans | Status | Completed |
|-------|-----------|-------|--------|-----------|
| 1. Render Pipeline | v1.0 | 1/1 | Complete | 2026-01-09 |
| 2. Analysis Core | v1.0 | 2/2 | Complete | 2026-01-09 |
| 3. Iteration Tools | v1.0 | 2/2 | Complete | 2026-01-09 |
| 4. Zwicker Model | v1.1 | 1/1 | Complete | 2026-01-09 |

---

*Last updated: 2026-01-09*
