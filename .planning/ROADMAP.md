# audio-loop Roadmap

## Milestone 1: Core System

### Phase 1: Core Infrastructure
**Goal:** CLI skeleton + SuperCollider rendering pipeline

**Deliverables:**
- `audioloop` CLI entry point (Python/typer)
- `audioloop render <file.scd>` command
- SC code execution via sclang subprocess
- WAV file capture and validation
- Basic error handling for SC failures

**Research:** None

---

### Phase 2: Analysis Pipeline
**Goal:** Feature extraction and rich output formatting

**Deliverables:**
- `audioloop analyze <file.wav>` command
- librosa-based feature extraction (spectral, temporal, perceptual)
- Structured JSON output for Claude parsing
- Human-readable formatted output with sparklines
- `audioloop spectrogram` (ASCII representation)
- Zwicker psychoacoustic metrics (roughness, sharpness, fluctuation)

**Research:** Zwicker model implementation options

---

### Phase 3: Feedback Loop
**Goal:** Iteration with EXPECT verification

**Deliverables:**
- Parse `// EXPECT:` comments from SC code
- Verification engine comparing expectations to analysis
- `audioloop compare <a.wav> <b.wav>` for side-by-side
- `audioloop play <file.wav>` for system player
- Session management (`audioloop session start|list|show`)
- Iteration narration format

**Research:** None

---

### Phase 4: Descriptor Discovery
**Goal:** A/B workflow and experiment tracking

**Deliverables:**
- Descriptor functions (warm, bright, fuzzy, etc.) returning confidence scores
- A/B comparison workflow
- Experiment tracking via tk (markdown files)
- Query interface for learned mappings
- Reference sound generation on-demand

**Research:** tk experiment file format
