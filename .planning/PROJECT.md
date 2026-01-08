# audio-loop

AI-driven audio synthesis with verification feedback. Describe a sound, generate it, verify it matches.

## Vision

Create a closed-loop system where Claude Code:
1. Receives natural language sound descriptions ("fuzzy bass with wide stereo, rough then smooth")
2. Generates SuperCollider synthesis code
3. Renders audio to file
4. Analyzes output with Python (librosa/Essentia) + spectrogram visualization
5. Compares analysis to description criteria
6. Iterates until verification passes

The key innovation: treating audio analysis as a "test suite" for generative sound code.

## Requirements

### Validated

(None yet - ship to validate)

### Active

**Core Loop**
- [ ] SuperCollider code generation from descriptions
- [ ] Audio rendering via sclang CLI
- [ ] Python analysis pipeline (25-30 features)
- [ ] Spectrogram visualization for Claude inspection
- [ ] Iterative refinement based on analysis feedback

**Analysis Features**
- [ ] Spectral: centroid, rolloff, flux, flatness, bandwidth
- [ ] Pitch: f0 tracking, harmonicity, inharmonicity
- [ ] Amplitude: RMS, envelope shape, dynamics
- [ ] Temporal: onset detection, attack/decay characteristics
- [ ] Stereo: mid/side ratio, correlation, phase coherence, width
- [ ] Perceptual: MFCCs, loudness, roughness

**Descriptor System**
- [ ] Python functions for descriptor verification (is_warm, is_bright, etc.)
- [ ] Hybrid approach: formal vocabulary + Claude interpretation
- [ ] Temporal descriptors (swells, fades, pulsing)
- [ ] A/B comparison workflow for refining mappings

**Recipe Templates**
- [ ] Sound type organization: pads/, leads/, bass/, percussion/, fx/
- [ ] Each template includes SC code + expected measurements
- [ ] Context7 integration for SC documentation lookup

**Experiment Tracking**
- [ ] tk tickets for tracking descriptor experiments
- [ ] A/B comparison results
- [ ] Feature evolution history

### Out of Scope

- Complex music/arrangement - focus on single sounds
- GUI/web interface - CLI only, Claude Code as interface
- Static reference library - generate references on demand

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| SuperCollider over Csound/Faust | Mature, real-time capable, good headless support | SC via sclang CLI |
| External analysis (librosa) over SC built-in | Better visualization, more flexible, easier to extend | Python pipeline |
| Full stereo analysis | Essential for modern sound design, "width" is common descriptor | Include from start |
| Extensive features (25-30) | Can't discover what matters without having features to test | Comprehensive suite |
| Python functions for descriptors | More programmable than static mappings, Claude can extend | Code over config |
| tk for experiment tracking | Simple markdown files, easy to version and inspect | `.tickets/` |
| A/B comparison for mapping refinement | Matches human perception, easier than absolute ratings | Comparative workflow |
| Context7 for both reference + runtime | Build pattern library AND lookup docs during generation | Dual use |
| Iterate until success | Autonomous refinement, only fail on hard errors | High autonomy |
| Always explain verification reasoning | Transparency builds trust, helps debugging | Full reasoning |

## Constraints

- SuperCollider already installed
- Python/librosa needs setup
- macOS (darwin) platform
- CLI-only workflow

## Success Criteria

Proof of concept succeeds when:
**Claude demonstrates iterative refinement** - generates a sound, analyzes it, identifies mismatch ("centroid too high"), adjusts code, tries again, succeeds.

---
*Last updated: 2026-01-07 after initialization*
