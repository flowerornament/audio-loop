# audio-loop Learnings

Insights from sound design sessions and development.

---

## Session: 2026-01-09 (First Real Test)

### Key Finding: Analysis Enables Data-Driven Iteration

The Hecker experiment proved the toolkit's value:
- **v1**: Accelerating clicks + FFT noise. Roughness: 2.658 asper
- **v2**: Gendy (aperiodic) synthesis. Roughness dropped to **0.041 asper**
- **v3**: Added Latch.ar + gates + bit reduction. Roughness back to **3.699 asper**

Without the roughness metric, the v1→v2 change would have seemed like an improvement ("more aperiodic = more Hecker"). The numbers revealed that Gendy is temporally smooth despite being spectrally chaotic. This led to a targeted fix.

**Lesson**: Metrics reveal non-obvious trade-offs. Don't assume conceptual changes produce expected results.

---

## Performance: Iteration Loop Bottlenecks (Updated 2026-01-11)

### What Phase 5 Profiling Revealed

Analysis timing for 6-second audio:
- **Full analysis (with psychoacoustic):** ~8s
- **Fast analysis (--no-psychoacoustic):** ~1s
- **MoSQITo loudness_zwtv:** 79% of analysis time, scales linearly with audio duration

Parallelization was tested and **rejected** - ProcessPoolExecutor spawn overhead (~500ms) exceeded potential savings (~200-300ms from roughness).

### What Real-World Testing Revealed

End-to-end "describe → render → analyze → play" loop: **38 seconds**

| Component | Time | Notes |
|-----------|------|-------|
| Claude thinking + writing SC code | ~8s | Inherent to the task |
| Tool call overhead (4 round-trips) | ~14s | **This is the real bottleneck** |
| Render | 2.3s | Mostly sclang startup |
| Analyze | ~8s | MoSQITo dominates |
| Play | 6s | Actual audio duration |

**Key insight:** The analysis code is fine. The orchestration overhead (multiple tool calls, process startups) is the real problem.

### High-Impact Optimizations Identified

1. **`audioloop iterate` command** - Single CLI that takes SC code, renders, analyzes, plays. Eliminates temp file dance and reduces Claude to 1 tool call.

2. **Daemon mode** - Keep sclang warm. Current 2.3s render is mostly startup. A persistent process could render in milliseconds.

3. **Inline SC code** - Accept code as argument or stdin, not just file paths.

4. **Combined output** - Single JSON blob with render status + analysis + file path.

**Workaround (now):** Use `--no-psychoacoustic` for rapid iteration, full analysis at checkpoints.

---

## Prompting: Lean on Reference Knowledge

Claude knows more than expected about experimental musicians, synthesis techniques, and aesthetic movements.

**What works**:
- Specific artist names: "Florian Hecker", "Xenakis", "Autechre"
- Album/track references
- Aesthetic movements: "spectralism", "granular", "glitch"
- Technical lineage: "Xenakis → IRCAM → Hecker"

**What doesn't work as well**:
- Generic descriptions without reference points
- Assuming Claude understands implicit aesthetic constraints

The initial Hecker attempt used periodic structures (Impulse, SinOsc panning). Once the anti-periodicity constraint was explicit, the approach improved significantly.

---

## Sophistication: Push for More

First attempts tend to be "correct but unsophisticated" — generic synthesis techniques that technically match the description but lack depth.

**To improve**:
- Don't settle for "working" — push for "good"
- Layer multiple techniques (Gendy + FFT + granular + temporal rupture)
- More iterations, more refinement
- Ask "what would make this more [artist-like]?" not just "does this work?"

---

## Technique Library (SuperCollider)

### Aperiodic Synthesis
```supercollider
// Gendy - Xenakis stochastic synthesis
Gendy1.ar(ampdist, durdist, adparam, ddparam, minfreq, maxfreq)
Gendy2.ar(...)  // More parameters

// Aperiodic triggers (NOT Impulse)
Dust.ar(density)  // Random impulses
Dust2.ar(density) // Bipolar

// All modulation via noise
LFNoise0.kr(freq)  // Sample-and-hold
LFNoise1.kr(freq)  // Linear interp
LFNoise2.kr(freq)  // Quadratic interp
```

### Temporal Discontinuity
```supercollider
// Sample-and-hold on signal
Latch.ar(signal, Dust.ar(rate))

// Random gates
Trig.ar(Dust.ar(rate), duration)

// Bit reduction
(signal * N).round / N
```

### Spectral Chaos
```supercollider
chain = FFT(LocalBuf(2048), signal);
chain = PV_Freeze(chain, freeze_flag);
chain = PV_MagSmear(chain, num_bins);
chain = PV_BinShift(chain, stretch, shift);
chain = PV_BinScramble(chain, wipe, width, trigger);
IFFT(chain)
```

---

## Analysis Interpretation Guide

| Metric | Low Value | High Value | Use For |
|--------|-----------|------------|---------|
| Roughness (asper) | 0 = smooth | >1 = rough/gritty | Temporal harshness, transients |
| Flatness | 0 = tonal | 1 = noise-like | Pitched vs noise content |
| Centroid (Hz) | Low = dark | High = bright | Spectral brightness |
| Stereo Correlation | 0 = decorrelated | 1 = mono | Stereo independence |
| Sharpness (acum) | Low = dull | High = bright/harsh | High-frequency perception |
| Crest Factor | Low = compressed | High = dynamic | Transient density |

---

## Future Features (High Value)

### Spectrogram Over Time
Would let Claude see texture evolution, not just aggregate metrics. Critical for understanding:
- How sounds develop
- Where transitions happen
- Temporal structure

### Reference Comparison
"Make it sound like [reference.wav]" — analyze both, compare, iterate toward target.

### Faster Iteration Loop
See "Performance: Iteration Loop Bottlenecks" above. The `audioloop iterate` command is the highest-impact optimization.

---

*Last updated: 2026-01-11*
