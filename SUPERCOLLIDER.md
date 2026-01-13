# SuperCollider Patterns

Reference for common SC idioms. These are patterns that work - use what fits.

## File Styles

### Quick test style
Good for rapid iteration:
```supercollider
(
{
    // synthesis here
}.play;
)
```

### Modular style
Good when user wants to add/remove/tweak synths independently:
```supercollider
s.boot;
// SynthDefs, Buses, Groups, Synths in separate blocks
// Store synth refs in ~variables for .free and .set
```

## Common Patterns

### Variable declarations
SC requires all `var` at the top of a function block:
```supercollider
{
    var a, b, c;
    a = SinOsc.ar(440);
    // ...
}
```

### Bus routing
```supercollider
~bus = Bus.audio(s, 2);
// Write: Out.ar(~bus, sig)
// Read: In.ar(~bus, 2)
```

### Groups for ordering
```supercollider
~src = Group.new;
~fx = Group.after(~src);
// Sources in ~src, effects in ~fx
```

### Triggered events
```supercollider
Ringz.ar(Dust.ar(2), 1000, 0.1)  // random triggers
sig * Decay2.ar(Impulse.ar(1), 0.01, 0.3)  // regular triggers
```

### Noise bands
```supercollider
LPF.ar(BrownNoise.ar, 60)   // sub rumble
HPF.ar(WhiteNoise.ar, 8000) // high shimmer
BPF.ar(PinkNoise.ar, 1000, 0.3) // mid band
```

### Modulation
```supercollider
LFNoise1.kr(0.1).exprange(200, 800)  // smooth random
LFNoise0.kr(0.5).exprange(200, 800)  // stepped random
thing.lag(2)  // smooth changes over 2 sec
```

### Stereo
```supercollider
Pan2.ar(sig, pan)
Splay.ar(array, spread)
sig * [1, 1]  // mono to stereo
freq * [1, 1.005]  // detune for width
```

## Debugging

- **Silent?** Check bus routing, group order, amplitude
- **SynthDef not found?** Run the SynthDef block first, check for syntax errors
- **Rate mismatch?** Use `.ar` triggers for `.ar` UGens (e.g., `Dust.ar` not `Dust.kr` for `Ringz.ar`)

## Notes

- These are reference patterns, not requirements
- SC is flexible - there are many valid approaches
- Add patterns you discover to this file
