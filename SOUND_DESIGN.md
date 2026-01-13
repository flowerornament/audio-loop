# Sound Design Notes

Learnings from iterative sessions. These are options and approaches that worked well - not rules. Future agents should treat these as starting points and add their own discoveries.

## Approaches That Worked

### Extremes as a creative tool
Pushing parameters "too far" often led to more interesting results than careful moderation. When the limiter starts working hard, it becomes part of the sound.

### Collaborative iteration
Simple files that the user could edit directly in SuperCollider were more engaging than elaborate auto-pilot compositions. Consider giving canvases with exposed parameters rather than finished pieces.

### Texture over realism
When simulating environments (rainforest, etc.), abstract textures and "wrong" sounds sometimes felt more evocative than accurate recreation.

## Frequency Approaches

### Band thinking (one way to organize)
- Sub: < 80Hz
- Bass-mids: 80-250Hz
- Mids: 250-2kHz
- High-mids: 2-4kHz
- Highs: > 4kHz

### Sub-bass management options
- Mono summing below ~80Hz avoids phase cancellation
- "Ownership gating" - letting the loudest source own the sub
- Keeping sub content dry (no reverb) can reduce mud
- Compressing a dedicated sub bus can glue sources

### The "donut hole"
One approach: put energy only at extreme lows and extreme highs, nothing in between. Creates unusual tension.

## Modulation Time Scales

Different rates create different feelings:
- Fast (5-20 Hz): tremolo, texture
- Medium (0.1-1 Hz): breathing, organic movement
- Slow (0.01-0.1 Hz): evolution over minutes
- Glacial (0.001-0.01 Hz): changes over 2-15 minutes

Global modulators (shared "breath" across layers) can create cohesion.

## Techniques Worth Knowing

### Granular territory
- High event rates (50-500/sec)
- Very short decays (< 1ms)
- Can create dense textures

### FM-adjacent sounds
Pushing vibrato ranges far beyond subtle pitch wobble (e.g., `freq * LFNoise1.kr(10).range(3, 6)`) creates metallic sidebands.

### Saturation before limiting
Running hot into `.tanh` or similar before the limiter adds glue.

## Artist-Specific Approaches

### Caterina Barbieri style
- **Repetition over variation**: 4-8 note patterns cycling hypnotically
- **Negative counterpoint**: Full pattern exists, random gates subtract notes (85-95% gate probability)
- **Two oscillators, distinct roles**: Harmonic oscillator for melody, DPO for texture
- **Delay as counterpoint**: >300ms delays become independent voices
- **Cross-modulation**: Everything modulates something (Maths→Maths rate, etc.)
- Reference: centroid ~2500 Hz, flatness <0.002

### Florian Hecker style
- **Anti-periodicity**: No Impulse, no regular LFOs - use Dust, LFNoise
- **Temporal rupture**: Latch.ar for stairstepping, random gates for cuts
- **Gendy caveat**: Spectrally chaotic but temporally smooth - add ruptures for roughness

## Metric Interpretation

| Metric | Low | High | Notes |
|--------|-----|------|-------|
| Centroid | dark | bright | Barbieri ~2500Hz, warm pads ~600Hz |
| Roughness | smooth | gritty | Fire needs >1.5 asper |
| Flatness | tonal | noisy | <0.01 for pitched content |

## Key Learning: First Attempts Often Best

Observed across sessions: later iterations frequently sound worse despite "better" metrics. When something sounds right, stop. Don't chase numbers.

## Notes for Future Agents

- These are options, not requirements
- Add your own learnings to this file
- What works depends heavily on context and user intent
- Ask the user what direction they want before assuming
- See `.learnings/sound-design-journal.md` for session histories
