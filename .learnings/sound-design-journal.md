# Sound Design Learning Journal

A running log of learnings from sound synthesis sessions with audioloop.

---

## Core Principles (Evolved from Sessions)

### The Tool is a Diagnostic, Not a Prescription

Like a blood pressure monitor: tells you something's off, doesn't tell you to exercise more. You need domain knowledge to translate readings into action.

Metrics said "centroid too low." A producer would think "boost 2-4k, add saturation." I thought "add more oscillators." Same data, different interpretation.

### Iterate Toward Sound, Not Metrics

When something sounds right, stop. Metrics measure one thing; perception is another. Chasing numbers leads to over-engineering and worse results.

Pattern observed: **First attempts are often among the best.** Later attempts may be spectrally closer to targets but sound more primitive/amateur.

### Identify the Craft First

**Step 0 should be: What role am I playing here?**

| Task | Role | Approach |
|------|------|----------|
| Fire ambience | Foley artist | Layer natural elements, focus on texture |
| XTAL-style ambient | 90s electronic producer | Gear chains, mixing, saturation, studio craft |
| Star Wars blaster | Movie sound designer | Record real sounds, layer, pitch shift, processing |
| Video game UI | Game audio designer | Clarity, responsiveness, feedback, short transients |
| Generative installation | Experimental sound artist | Systems, emergence, texture, happy accidents |

Don't jump straight to "SuperCollider oscillators" without asking "what would the appropriate practitioner do here?"

### Use Metrics as Sanity Checks, Not Primary Targets

They're symptoms, not goals. Metrics reveal non-obvious trade-offs, but optimizing directly for them produces hollow results.

---

## Session: 2026-01-11 - Fireplace Crackling

**Goal:** Create extremely realistic indoor fireplace sound

**Duration:** ~26 iterations over ~90 minutes

**Final output:** `sounds/fireplace.wav` (30s, -18.5 LUFS)

### What Worked

**Layered approach:** Building fire from distinct components (crackles, hiss, lapping, pops, ember) gave good control. Each layer addresses a different aspect of the sound.

**Using Dust.kr for triggers:** Random trigger generators are perfect for organic, non-rhythmic events like fire. The rate parameter directly controls density.

**BPF + percussive envelope pattern:** `BPF.ar(WhiteNoise.ar, freq, rq) * EnvGen.ar(Env.perc(...))` is a workhorse for transient sounds. Varying freq and duration per trigger creates variety.

**Pan2 for spatial distribution:** Even though correlation measurements showed "mono," the transient events (pops, crackles) do have spatial character. The continuous low-frequency content just dominates the measurement.

**Spectrogram analysis:** The mel spectrogram immediately revealed problems I couldn't hear in the metrics:
- Comb filtering showed as horizontal bands
- Spectral balance issues were visually obvious
- Chromagram showed tonal content (or lack thereof)

### What Didn't Work

**Artificial stereo widening hacks:**
- CombL filters created audible comb filtering artifacts
- Mid-side encoding with GrayNoise differences added harshness
- Trying to "force" stereo made things worse, not better

**Over-engineering:** I spent many iterations trying to solve a "stereo problem" that wasn't really a problem. The measurements were misleading because continuous bass dominates correlation calculations.

**Too many Mix.fill voices:** SuperCollider NRT mode has complexity limits. 8+ layers or 15+ voices per layer caused "SynthDef not found" errors. Had to stay under ~10-12 voices per layer, ~6 layers total.

**Rand() in NRT mode:** Random values generated with Rand() during SynthDef compilation are the same for "independent" channels because NRT uses a fixed seed. This made my attempts at "truly independent L/R" produce correlated output.

### Tool Usage Reflections

**audioloop iterate:** Very useful for rapid iteration. The JSON output gave me metrics to work with, and auto-play let me hear results immediately.

**What was slow:**
- Each render took ~2-3 seconds plus ~30s of playback
- Spectrogram generation sometimes timed out on longer files
- No way to A/B compare iterations quickly without manual file management

**What was fast:**
- The feedback loop itself: write code → render → hear → see metrics
- Having all metrics in one JSON blob

**Tool gaps I noticed:**
- No spectral comparison between iterations (would have caught comb filtering faster)
- Stereo correlation measurement is misleading for sounds with transient stereo content but continuous mono content
- Would be nice to render shorter test clips during iteration, then final long version

### Process Reflections

**I over-relied on metrics:** I kept chasing "stereo width" numbers when I should have trusted my ears and your feedback that the stereo was actually fine. The metrics measure one thing; perception is another.

**I under-used spectrograms:** You had to prompt me to look at them. The spectrogram immediately showed the comb filtering issue. I should have been checking spectrograms every few iterations, not just when stuck.

**I didn't check for tonal content early enough:** You had to remind me about "tonal creep." The chromagram was available the whole time - I should have been monitoring it.

**My iteration strategy was reactive:** I'd fix one problem, create another, fix that, etc. A more methodical approach would have been:
1. Get the basic texture right (spectral balance)
2. Get the dynamics right (pops vs continuous)
3. Then worry about stereo
4. Check for artifacts last

Instead I jumped around between concerns.

### How Prompting Could Have Helped Me

**Early constraints would have saved time:**
- "Don't try to artificially widen stereo - Pan2 is enough"
- "Check the spectrogram every 3 iterations"
- "Focus on texture depth over stereo width"

**Specific targets would have focused iteration:**
- "Aim for centroid around 1200-1500 Hz"
- "Roughness should be above 1.5 for good crackle texture"
- "Band energies should show sub dominant but with visible mid presence"

**Asking me to explain my approach before implementing:**
- If you'd asked "why are you adding comb filters?" I might have realized it was a bad idea before wasting iterations on it

### How I Could Have Done Better

1. **Asked more questions upfront:** What makes a fire sound "realistic" to you? Indoor vs outdoor? Roaring vs dying? This would have constrained the problem.

2. **Made a test plan:** Instead of 26 ad-hoc iterations, I could have systematically tested: layer balance → spectral shape → dynamics → stereo → artifacts.

3. **Saved named checkpoints:** Instead of iterate_001 through iterate_026, I should have saved meaningful versions like "fire_warm_base.wav", "fire_with_pops.wav" etc.

4. **Read the spectrogram more often:** Visual inspection caught problems that metrics missed.

5. **Trusted simpler solutions:** The cleanest version (just Pan2 on transients, centered bass) sounded best. The complexity I added (comb filters, mid-side) made things worse.

### Technical Learnings for Future Sound Design

**Fire specifically:**
- Needs layers at different time scales: rapid micro-pops, medium crackles, slow settling, continuous hiss/rumble
- Low-frequency content provides "body" and warmth
- Transients need attack clicks (short high-freq burst) to sound woody
- Dust.kr rates: 0.1-0.5 for big events, 1-5 for crackles, 8+ for rapid sparkle

**General synthesis:**
- BPF bandwidth (rq) controls how "resonant" vs "noisy" a filtered noise sounds
- Env.perc curve parameter: more negative = snappier attack character
- TExpRand vs TRand: exponential gives better frequency distributions
- DelayN under 1ms avoids comb artifacts but doesn't create much stereo
- GrayNoise, ClipNoise, etc. have very different spectral characteristics

**SuperCollider NRT gotchas:**
- SynthDef complexity limits exist - keep it simple
- Rand() values are fixed at compile time
- Multi-channel expansion with ! works but stereo arrays need care

### Post-Session Note (from user feedback)

**The first attempt was one of the best ones.**

This is significant. I had 26 iterations and arguably made things worse, not better. The first attempt had:
- Clean layered structure
- No artificial stereo hacks
- Simple, readable code

What happened: I saw "stereo width: 0.0001" in the metrics and assumed it was broken. I then spent 20+ iterations "fixing" something that wasn't broken, introducing actual problems (comb filtering, spectral imbalance, complexity) along the way.

**The lesson:** When something sounds right, stop. Don't iterate toward metrics. Iterate toward sound. If I had listened more and measured less, I would have been done in 3-4 iterations, not 26.

This is probably the most important learning from this session.

### Questions for Next Time

- How do I create true stereo decorrelation in NRT mode?
- Is there a better way to measure "transient stereo" vs "continuous stereo"?
- What's the right centroid range for different sound types?
- How do I know when roughness is "too much"?

---

## Session: 2026-01-10 - IDM/Aphex Twin Style Beat

**Goal:** Create beat-based IDM thing (Aphex Twin style)

### Key Discovery: Wrong Reference Entirely

Asked to make "Aphex-style IDM." Ended up comparing to XTAL, which is from SAW85-92 — ambient era, completely different from Drukqs-era chaos I was targeting.

| Metric | XTAL | My Attempt |
|--------|------|------------|
| Roughness | 0.075 (smooth) | 1.08 (rough) |
| Sub bass | 0.44 | 0.01 |
| Character | Continuous flowing | Isolated transients with silence |

Without the compare workflow, I would have thought "this sounds IDM-ish" and moved on. The tool caught that I was making the wrong thing.

### The Spectrogram Showed Why

Numbers told me roughness differed; the spectrogram showed *why* — XTAL is continuous flowing energy, mine was isolated transients with silence between.

**Visual + numeric together > either alone.**

### Iteration Toward XTAL

| Metric | XTAL | v1 | v2 | v3 |
|--------|------|-----|-----|-----|
| Roughness | 0.075 | 1.08 | 0.083 | 0.056 |
| Centroid | 2491 Hz | 3117 Hz | 375 Hz | 535 Hz |

Got metrics closer but **sounds were amateur**. Even when numbers matched, the *sound* was primitive — "basic synthesizers with no mix, no chain, no effects."

### Critical User Feedback

Real production involves:
- End-of-chain compression, saturation
- Per-element processing chains
- Sound selection and deep sound design
- "Abusing" gear — pushing things non-linearly
- Years of ear training

My approach: raw oscillators → mix → output. That's not production.

**Key insight:** "I'm not sure you lack the production knowledge — if I prompt you correctly, you might know everything about production."

The gap isn't knowledge. It's **application without prompting.**

### Why First Attempt Was Arguably Best

It sounded like *something intentional* (even if wrong genre). Later attempts were spectrally closer but more primitive-sounding.

---

## Session: 2026-01-09 - Florian Hecker Experiment

**Goal:** Create Hecker-style experimental sound

### Metrics Reveal Non-Obvious Trade-offs

| Version | Approach | Roughness |
|---------|----------|-----------|
| v1 | Accelerating clicks + FFT noise | 2.658 asper |
| v2 | Gendy (aperiodic) synthesis | 0.041 asper |
| v3 | Added Latch.ar + gates + bit reduction | 3.699 asper |

Without the roughness metric, the v1→v2 change would have seemed like an improvement ("more aperiodic = more Hecker"). The numbers revealed that **Gendy is temporally smooth despite being spectrally chaotic.**

**Lesson:** Don't assume conceptual changes produce expected results. Measure.

### Prompting Insight: Lean on Reference Knowledge

Claude knows more than expected about experimental musicians, synthesis techniques, and aesthetic movements.

**What works:**
- Specific artist names: "Florian Hecker", "Xenakis", "Autechre"
- Album/track references
- Aesthetic movements: "spectralism", "granular", "glitch"
- Technical lineage: "Xenakis → IRCAM → Hecker"

**What doesn't work:**
- Generic descriptions without reference points
- Assuming implicit aesthetic constraints

The initial Hecker attempt used periodic structures (Impulse, SinOsc panning). Once the **anti-periodicity constraint was explicit**, the approach improved significantly.

---

## Analysis Interpretation Quick Reference

| Metric | Low Value | High Value | Use For |
|--------|-----------|------------|---------|
| Roughness (asper) | 0 = smooth | >1 = rough/gritty | Temporal harshness, transients |
| Flatness | 0 = tonal | 1 = noise-like | Pitched vs noise content |
| Centroid (Hz) | Low = dark | High = bright | Spectral brightness |
| Stereo Correlation | 0 = decorrelated | 1 = mono | Stereo independence |
| Sharpness (acum) | Low = dull | High = harsh | High-frequency perception |
| Crest Factor | Low = compressed | High = dynamic | Transient density |

**Warning:** Stereo correlation misleads when transient content has spatial character but continuous content is mono. Listen, don't just measure.

---

## SuperCollider Technique Library

### Aperiodic Synthesis
```supercollider
// Gendy - Xenakis stochastic synthesis
Gendy1.ar(ampdist, durdist, adparam, ddparam, minfreq, maxfreq)

// Aperiodic triggers (NOT Impulse)
Dust.ar(density)   // Random impulses
Dust2.ar(density)  // Bipolar

// Noise-based modulation
LFNoise0.kr(freq)  // Sample-and-hold
LFNoise1.kr(freq)  // Linear interp
LFNoise2.kr(freq)  // Quadratic interp (smoothest)
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

### Spectral Processing
```supercollider
chain = FFT(LocalBuf(2048), signal);
chain = PV_Freeze(chain, freeze_flag);
chain = PV_MagSmear(chain, num_bins);
chain = PV_BinShift(chain, stretch, shift);
chain = PV_BinScramble(chain, wipe, width, trigger);
IFFT(chain)
```

### Fire/Ambience Pattern
```supercollider
// Transient events
Mix.fill(N, {|i|
    var trig = Dust.kr(rate);
    var env = EnvGen.ar(Env.perc(attack, TRand.kr(minDur, maxDur, trig)), trig);
    var freq = TExpRand.kr(minFreq, maxFreq, trig);
    Pan2.ar(BPF.ar(WhiteNoise.ar, freq, rq) * env, TRand.kr(-1, 1, trig));
}).sum

// Continuous body
LPF.ar(BrownNoise.ar, cutoff) * LFNoise2.kr(modRate).range(minAmp, maxAmp)
```

---

## Workflow Recommendations

1. **Analyze reference FIRST** — Before synthesizing anything, understand the target
2. **Identify the craft** — "What role am I playing?" before "What oscillators should I use?"
3. **Check spectrogram every 3-5 iterations** — Visual catches what numbers miss
4. **Save meaningful checkpoints** — Not iterate_001, but fire_warm_base.wav
5. **Trust early versions** — If it sounds right, stop. Don't chase metrics.
6. **Compare workflow is powerful** — Always have a reference to compare against

---

## Session: 2026-01-11 - Caterina Barbieri Recreation

**Goal:** Recreate Barbieri's synthesis setup and compose in her style

**Duration:** ~10 iterations over ~2 hours

**Final outputs:** `sounds/barbieri/` directory

### Her Setup (From Research)

| Module | Role |
|--------|------|
| Verbos Harmonic Oscillator | 8 harmonics, additive synthesis |
| Make Noise DPO | Dual complex oscillator, FM creates saw-like richness |
| ER-101 Sequencer | Indexed patterns, mathematical operations |
| Maths | Function generators for envelopes/modulation |
| Optomix/LxD | Low pass gates with vactrol character |
| Echophon | Pitch-shifting delay (used sparingly) |
| Erbe-Verb | Reverb |
| Wogglebug | Random modulation |

### Key Technique: Negative Counterpoint

Her signature: The full pattern exists, but random gates **subtract notes**, revealing melodic subsets. What remains feels "discovered." High gate probability (~85-95%) means continuous flow, not sparse.

### Critical Learnings

**1. Modulation is Central to Modular**
Everything modulates something else:
- Maths1 → Maths2 rate, envelope times, filter freq
- Wogglebug → detune, gate probability, spectral tilt
- Slow LFOs → scan position, mix levels

Real modular patches feel "alive" because parameters are constantly moving.

**2. Two Oscillators Have Distinct Roles**
- Harmonic Oscillator: melodic voice, pure additive harmonics
- DPO: FM creates sawtooth-like richness, texture/body

**3. Delay Creates Counterpoint**
Long delays (>300ms) create true canonic counterpoint — the original line and its echoes become independent voices. This makes monophonic sound polyphonic.

**4. Her Music is REPETITIVE**
NOT random. Same 4-8 notes cycling hypnotically. The trance state comes from repetition. Variation comes from gate manipulation and slow modulation, not melody changes.

**5. West Coast = Timbre Over Pitch**
- LPG: filter tracks amplitude (vactrol character creates "ring")
- FM: creates rich harmonics dynamically
- Spectral evolution: slow tilt/scan modulation
- Touch-responsive, organic feel

**6. She's a COMPOSER**
Real melodies have: motifs, phrase structure (question/answer), cadences, direction. Not just cycling patterns but intentional composition.

### Reference Metrics

| Metric | Consciousness | Fantas | Target |
|--------|--------------|--------|--------|
| Centroid | 2508 Hz | 2535 Hz | ~2500 Hz |
| Flatness | 0.0015 | 0.0003 | < 0.002 |
| Sharpness | 1.46 acum | 1.53 acum | ~1.5 |

### What Worked

1. **Higher register patterns** → brighter centroid
2. **High gate probability (>85%)** → continuous flow
3. **Long envelope decays (500-800ms)** → notes blend
4. **Strong FM modulation (index 2-4)** → rich harmonics
5. **Multiple delay times** → dense wash
6. **Less harmonic rolloff (0.4-0.5 power)** → brightness

### What Didn't Work

1. **Too much negative counterpoint (sparse)** → not hypnotic
2. **Pitch-shifting delay as main effect** → she uses it sparingly
3. **Random patterns** → she's repetitive
4. **Too dark/warm** → target centroid is ~2500 Hz

### SuperCollider Patterns

```supercollider
// FM for rich harmonics (DPO-style)
dpoMod = 3; // Higher = more harmonics
dpoOsc2 = SinOsc.ar(freq + (dpoOsc1 * dpoMod * freq));

// LPG: filter tracks amplitude with vactrol lag
lpgFreq = Lag.ar(env, 0.02).linexp(0.001, 1, 400, 8000);

// Negative counterpoint
gateProb = 0.85;
gate = TRand.kr(0, 1, clock) < gateProb;

// Cross-modulation (modular style)
maths2Rate = maths1.linlin(0, 1, 0.1, 0.5);
maths2 = LFTri.kr(maths2Rate);
```

### Process Observation

The user's feedback was essential:
- "More repetitive, faster" → hypnotic_v1
- "Think about modulation" → modular_v1 with rich cross-patching
- "Hear the DPO" → bright_dpo_v1 with FM-forward mix
- "Make an actual melody" → composed_melody_v1 with phrase structure

Without prompts pushing toward specificity, I stayed at "correct but unsophisticated."

---

*Last updated: 2026-01-11*
