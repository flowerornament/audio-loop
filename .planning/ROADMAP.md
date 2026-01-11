# audio-loop Roadmap

## Milestones

- [v1.0 Working Feedback Loop](milestones/v1.0-ROADMAP.md) (Phases 1-3) SHIPPED 2026-01-09
- [v1.1 Psychoacoustics](milestones/v1.1-ROADMAP.md) (Phase 4) SHIPPED 2026-01-09
- [v2.0 Analysis Upgrades](milestones/v2.0-ROADMAP.md) (Phases 5-7) SHIPPED 2026-01-11
- 🚧 **v2.1 MCP Integration** — Phases 8-10 (in progress)

---

### 🚧 v2.1 MCP Integration (In Progress)

**Milestone Goal:** Make audioloop a proper MCP tool that Claude can use effectively without guessing flags or needing external documentation

#### Phase 8: MCP Server

**Goal**: Create Python MCP server wrapping audioloop CLI with full tool schemas
**Depends on**: v2.0 complete
**Research**: Likely (MCP protocol, Python SDK, tool schema patterns)
**Research topics**: MCP protocol specification, Python MCP server implementation, tool schema best practices
**Plans**: TBD

Plans:
- [ ] 08-01: TBD (run /gsd:plan-phase 8 to break down)

#### Phase 9: Skill Definition

**Goal**: Create skill with workflow guidance and best practices
**Depends on**: Phase 8
**Research**: Unlikely (internal patterns — Markdown documentation)
**Plans**: TBD

Plans:
- [ ] 09-01: TBD

#### Phase 10: Spectrogram Validation

**Goal**: Test whether Claude effectively uses spectrogram images to improve sound design decisions
**Depends on**: Phase 9
**Research**: Unlikely (testing methodology, not new tech)
**Plans**: TBD

Plans:
- [ ] 10-01: TBD

---

## Completed Milestones

<details>
<summary>v2.0 Analysis Upgrades (Phases 5-7) SHIPPED 2026-01-11</summary>

- [x] Phase 5: Performance Optimization (1/1 plans) completed 2026-01-11
- [x] Phase 5.1: CLI Iterate Command (1/1 plans) completed 2026-01-11
- [x] Phase 5.2: CLI Output UX Polish (1/1 plans) completed 2026-01-11
- [x] Phase 6: Spectrogram Visualization (1/1 plans) completed 2026-01-11
- [x] Phase 7: Real-World Validation (findings doc) completed 2026-01-11

**Delivered:** Faster iteration with `iterate` command, spectrogram visualization, and validation insight: "tool is diagnostic, not prescription"

[Full details](milestones/v2.0-ROADMAP.md)

</details>

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
| 7. Real-World Validation | v2.0 | N/A | Complete | 2026-01-11 |
| 8. MCP Server | v2.1 | 0/? | Not started | - |
| 9. Skill Definition | v2.1 | 0/? | Not started | - |
| 10. Spectrogram Validation | v2.1 | 0/? | Not started | - |

---

*Last updated: 2026-01-11 after v2.1 milestone creation*
