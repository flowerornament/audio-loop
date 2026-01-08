# audio-loop

An experimental system to discover which audio features correlate with subjective sound descriptors.

## The Problem

When you say a sound is "fuzzy" or "warm" or "rough then smooth" - what does that actually mean in measurable terms?

This project explores that question by building a feedback loop:
1. Describe a sound in natural language
2. Claude generates SuperCollider code
3. Render to audio file
4. Analyze with Python (librosa) - extract 25+ features
5. Compare analysis to description - does it match?
6. If not, Claude adjusts and tries again

The core hypothesis: **subjective audio descriptors can be mapped to combinations of measurable features**, and we can discover those mappings through iteration and A/B comparison.

## What We're Trying to Learn

The central research questions:

1. **Which features matter for which descriptors?**
   - "warm" might correlate with low spectral centroid - or maybe harmonic density - or both with weights
   - "fuzzy" might be spectral flatness - or noise content - or something we haven't considered
   - We don't know yet. That's the point.

2. **Can Claude interpret spectrograms meaningfully?**
   - Visual inspection adds information beyond numeric metrics
   - But can Claude actually "read" a spectrogram? Needs validation.

3. **How do we detect failure vs. "keep trying"?**
   - When is Claude stuck in a dead-end vs. making progress?
   - What signals indicate "this descriptor can't be verified with current features"?

## The A/B Workflow

When a descriptor mapping is uncertain:

1. Claude generates two sound variants with different interpretations
   - Version A: "warm" = centroid < 1kHz
   - Version B: "warm" = centroid < 1.5kHz + high harmonic ratio
2. Both get analyzed, you listen and pick which is "more warm"
3. Winning interpretation gets recorded in tk as an experiment result
4. Over time, patterns emerge about what features actually matter

This is how we learn - not by defining upfront, but by comparing and refining.

## Requirements

### Validated

(None yet - ship to validate)

### Active

**Core Loop**
- [ ] SuperCollider code generation from descriptions
- [ ] Audio rendering via sclang CLI (write .scd, execute, capture .wav)
- [ ] Python analysis pipeline with modular feature extraction
- [ ] Spectrogram generation for visual inspection
- [ ] Iteration loop with analysis-driven refinement

**Analysis Features** (starting set, expect to add more)

| Category | Features | Why |
|----------|----------|-----|
| Spectral | centroid, rolloff, flux, flatness, bandwidth, contrast | Brightness, texture, movement |
| Pitch | f0 tracking, harmonicity, inharmonicity | Tonal vs noisy, tuning |
| Amplitude | RMS, envelope (attack/decay/sustain/release), crest factor | Dynamics, punch |
| Temporal | onset strength, tempo, rhythm regularity | Rhythmic character |
| Stereo | mid/side ratio, L-R correlation, phase coherence | Width, imaging |
| Perceptual | MFCCs, loudness (LUFS), roughness, sharpness | How humans hear it |

**Descriptor System**
- [ ] Python functions that take analysis dict, return confidence score (0-1, not boolean)
- [ ] Initial vocabulary: warm, bright, dark, fuzzy, harsh, smooth, rough, wide, narrow, punchy, soft
- [ ] Temporal modifiers: swelling, fading, pulsing, evolving, static
- [ ] Mechanism for Claude to propose new features when descriptors don't map well

**Experiment Tracking (tk)**
- [ ] Each experiment = one attempt to map a descriptor to features
- [ ] Record: descriptor, feature weights tried, audio file, user feedback
- [ ] Query: "what have we learned about 'fuzzy'?"

**Reference Generation**
- [ ] On-demand: Claude creates a "known warm" sound from SC templates
- [ ] Analyze it, use as calibration target
- [ ] No static library - generate fresh each time

### Out of Scope (v1)

- Multi-sound compositions or arrangements
- GUI or web interface
- Real-time synthesis (focus on offline render-analyze loop)
- Pre-built "correct" mappings - we're discovering them

## Key Decisions

| Decision | Rationale |
|----------|-----------|
| SuperCollider via sclang CLI | Mature, scriptable, renders to file cleanly |
| Python/librosa for analysis | Rich feature set, good visualization, easy to extend |
| Confidence scores not booleans | "Close but too harsh" is useful signal; pass/fail loses nuance |
| A/B comparison over ratings | "Which is warmer?" easier than "rate warmth 1-10" |
| tk for experiments | Markdown files, git-tracked, queryable, simple |
| Iterate until success OR dead-end | Autonomous but with escape hatch |
| Always explain reasoning | Transparency for debugging and learning |

## Open Questions

Things we need to figure out during implementation:

1. **Dead-end detection**: How many iterations with no improvement = give up?
2. **Feature weighting**: Linear combination? Thresholds? Decision trees?
3. **Spectrogram usefulness**: Does Claude's visual analysis add value over metrics?
4. **Descriptor composability**: Can "warm AND punchy" be verified as conjunction?
5. **Context window management**: Long iteration loops may need summarization

## Constraints

- SuperCollider installed and working
- Python environment needs setup (librosa, numpy, matplotlib)
- macOS platform
- CLI workflow via Claude Code
- Audio rendered to files (no real-time audio I/O needed)

## Success Criteria

**Minimum viable success:**
Claude generates a "warm pad with slow attack", analyzes it, finds centroid too high, adjusts filter cutoff, re-renders, confirms improvement, iterates until metrics match - and the result actually sounds warm when you listen.

**Real success:**
We have 5+ descriptors with validated feature mappings, documented in tk experiments, and Claude can reliably generate sounds matching novel combinations of those descriptors.

**Stretch:**
Claude proposes a new analysis feature we didn't think of because existing features couldn't capture a descriptor.

---
*Last updated: 2026-01-07 - revised to emphasize research/discovery nature*
