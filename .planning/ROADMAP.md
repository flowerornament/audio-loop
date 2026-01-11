# audio-loop Roadmap

## Milestones

- [v1.0 Working Feedback Loop](milestones/v1.0-ROADMAP.md) (Phases 1-3) SHIPPED 2026-01-09
- [v1.1 Psychoacoustics](milestones/v1.1-ROADMAP.md) (Phase 4) SHIPPED 2026-01-09
- 🚧 **v2.0 Analysis Upgrades** - Phases 5-7 (in progress)

## Completed Milestones

<details>
<summary>v1.1 Psychoacoustics (Phase 4) SHIPPED 2026-01-09</summary>

- [x] Phase 4: Zwicker Model Integration (2/2 plans) completed 2026-01-09

**Delivered:** Perceptual audio metrics via MoSQITo/Zwicker model

[Full details](milestones/v1.1-ROADMAP.md)

</details>

<details>
<summary>v1.0 Working Feedback Loop (Phases 1-3) SHIPPED 2026-01-09</summary>

- [x] Phase 1: Render Pipeline (1/1 plans) completed 2026-01-09
- [x] Phase 2: Analysis Core (2/2 plans) completed 2026-01-09
- [x] Phase 3: Iteration Tools (2/2 plans) completed 2026-01-09

**Delivered:** Complete describe-render-analyze-listen-iterate workflow

[Full details](milestones/v1.0-ROADMAP.md)

</details>

---

## 🚧 v2.0 Analysis Upgrades (In Progress)

**Milestone Goal:** Make analysis faster and richer so the feedback loop tightens

#### Phase 5: Performance Optimization ✓

**Goal**: Profile psychoacoustic metrics, parallelize serial bottleneck, target sub-5s full analysis
**Depends on**: v1.1 complete
**Research**: Complete
**Plans**: 1/1 complete

Plans:
- [x] 05-01: Performance profiling and benchmarking (completed 2026-01-11)

#### Phase 5.1: CLI Iterate Command ✓

**Goal**: Single `audioloop iterate` command for render→analyze→play loop with inline SC code support
**Depends on**: Phase 5 (learnings from performance testing)
**Research**: n/a
**Plans**: 1/1 complete

**Context**: Real-world testing revealed orchestration overhead (multiple tool calls, process startups) is the actual bottleneck, not analysis code. This phase addresses that.

Plans:
- [x] 5.1-01: Add iterate command with inline SC code support (completed 2026-01-11)

#### Phase 5.2: CLI Output UX Polish ✓

**Goal**: Improve human-readable output formatting - table borders, alignment, colors that work across terminals
**Depends on**: Phase 5.1 (iterate command exists)
**Research**: Unlikely (Rich library features, terminal compatibility)
**Plans**: 1/1 complete

**Context**: During Phase 5.1 verification, user noted table borders were nice but got lost during ANSI code fixes. Dedicated phase to polish the UX without blocking core functionality.

Plans:
- [x] 5.2-01: Unified table styling with shared layout module (completed 2026-01-11)

#### Phase 6: Spectrogram Visualization ✓

**Goal**: PNG (stacked waveform/spectrogram/chroma) + ASCII energy bands + CLI integration
**Depends on**: Phase 5.1
**Research**: Complete
**Plans**: 1/1 complete

Plans:
- [x] 06-01: Spectrogram PNG generation and ASCII frequency bands (completed 2026-01-11)

#### Phase 7: Real-World Validation

**Goal**: Sound design sessions to verify the loop tightened - iteration speed, feedback richness, outcome quality
**Depends on**: Phase 6
**Research**: Unlikely (user testing, not code implementation)
**Plans**: TBD

Plans:
- [ ] 07-01: TBD (run /gsd:plan-phase 7 to break down)

---

## Progress

| Phase | Milestone | Plans | Status | Completed |
|-------|-----------|-------|--------|-----------|
| 1. Render Pipeline | v1.0 | 1/1 | Complete | 2026-01-09 |
| 2. Analysis Core | v1.0 | 2/2 | Complete | 2026-01-09 |
| 3. Iteration Tools | v1.0 | 2/2 | Complete | 2026-01-09 |
| 4. Zwicker Model | v1.1 | 2/2 | Complete | 2026-01-09 |
| 5. Performance Optimization | v2.0 | 1/1 | Complete | 2026-01-11 |
| 5.1 CLI Iterate Command | v2.0 | 1/1 | Complete | 2026-01-11 |
| 5.2 CLI Output UX Polish | v2.0 | 1/1 | Complete | 2026-01-11 |
| 6. Spectrogram Visualization | v2.0 | 1/1 | Complete | 2026-01-11 |
| 7. Real-World Validation | v2.0 | 0/? | Not started | - |

---

*Last updated: 2026-01-11 after Phase 6 completion*
