// "Patterns Within Patterns" - West Coast Counterpoint
//
// Key ideas:
// 1. Two oscillators with SEPARATE ROLES and registers
// 2. Delays create CANON - original + echo become independent voices
// 3. Very slow HARMONIC EVOLUTION - chord changes over 30+ seconds
// 4. LPG character - filter tracks amplitude with vactrol "ring"
// 5. Negative counterpoint - gates subtract to reveal hidden melodies
// 6. Long delay times for true canonic counterpoint (not just echo)

{
    var dur = 180;  // 3 minutes - let it breathe
    var time = Line.kr(0, dur, dur);

    // VERY slow harmonic evolution - chord changes every ~40 seconds
    var harmPhase = (time / 40).floor;
    var rootNote = Select.kr(harmPhase % 4, [57, 60, 55, 57]);  // A, C, G, A

    var tempo, clock, masterClock;
    var melodicPattern, bassPattern;
    var melodicStep, bassStep;
    var melodicFreq, bassFreq;
    var melodicGate, bassGate;

    // Voice 1: Melodic (high register)
    var melodicHarmonics, melodicMix, melodicEnv, melodicLPG;

    // Voice 2: Bass (low register) - slower, more sustained
    var bassOsc, bassEnv, bassLPG;

    // Delay network for counterpoint
    var dryMelodic, dryBass, dry;
    var canon1, canon2, canon3;  // Canonic voices
    var delayMix, verb, out;

    tempo = 4.5;
    clock = Impulse.kr(tempo);
    masterClock = Impulse.kr(tempo * 0.25);  // Bass clock

    // === MELODIC PATTERN ===
    // Relative to root, creating modes
    // Very simple: just 5ths and octaves to start
    melodicPattern = [0, 7, 12, 7, 0, 5, 7, 12, 7, 5, 0, -5, 0, 7, 12, 7];
    melodicStep = Stepper.kr(clock, 0, 0, melodicPattern.size - 1);
    melodicFreq = (rootNote + Select.kr(melodicStep, melodicPattern)).midicps;

    // Gate probability modulates slowly - breathes in and out
    melodicGate = TRand.kr(0, 1, clock) < (0.75 + (SinOsc.kr(0.03) * 0.2));

    // === BASS PATTERN ===
    // Root and fifth, very simple, slower
    bassPattern = [0, 0, 7, 0];
    bassStep = Stepper.kr(masterClock, 0, 0, bassPattern.size - 1);
    bassFreq = (rootNote - 12 + Select.kr(bassStep, bassPattern)).midicps;

    bassGate = TRand.kr(0, 1, masterClock) < 0.9;

    // === VOICE 1: MELODIC HARMONIC OSCILLATOR ===
    melodicHarmonics = 8.collect { |i|
        var harmonicNum = i + 1;
        var harmonicFreq = melodicFreq * harmonicNum;
        // Gentle spectral evolution
        var tilt = SinOsc.kr(0.04).range(-0.2, 0.2);
        var amp = (harmonicNum / 4).pow(tilt) / harmonicNum.pow(0.65);
        SinOsc.ar(harmonicFreq) * amp;
    };
    melodicMix = Mix(melodicHarmonics);

    // LPG envelope - percussive but with ring
    melodicEnv = EnvGen.ar(
        Env.perc(0.005, 0.6, 1, -4),
        melodicGate * clock
    );

    // LPG: filter tracks amplitude with lag (vactrol)
    melodicLPG = RLPF.ar(
        melodicMix,
        Lag.ar(melodicEnv, 0.02).linexp(0.001, 1, 400, 7000),
        0.5
    ) * melodicEnv;

    dryMelodic = melodicLPG * 0.35;

    // === VOICE 2: BASS (SIMPLE OSCILLATOR) ===
    bassOsc = SinOsc.ar(bassFreq) + (SinOsc.ar(bassFreq * 2) * 0.3);

    bassEnv = EnvGen.ar(
        Env.perc(0.015, 1.8, 1, -3),  // Long decay
        bassGate * masterClock
    );

    bassLPG = LPF.ar(bassOsc, Lag.ar(bassEnv, 0.03).linexp(0.001, 1, 100, 600)) * bassEnv;

    dryBass = bassLPG * 0.4;

    // === COMBINE DRY SIGNALS ===
    dry = dryMelodic + dryBass;

    // === CANONIC DELAY NETWORK ===
    // Long delays create true counterpoint - echoes become voices
    // Each delay is at a musically meaningful interval

    // Canon 1: 1.5 beats later (dotted quarter)
    canon1 = CombL.ar(dryMelodic, 2, 0.333, 6) * 0.55;

    // Canon 2: 2 beats later (half note) - creates call/response
    canon2 = CombL.ar(dryMelodic, 2, 0.444, 5.5) * 0.45;

    // Canon 3: 4 beats later (whole note) - creates longer phrases
    canon3 = CombL.ar(dryMelodic, 2, 0.889, 7) * 0.35;

    // Stereo spread through ping-pong arrangement
    delayMix = [
        canon1 + (canon3 * 0.6),
        canon2 + (canon1 * 0.5)
    ];

    // === VAST REVERB ===
    verb = FreeVerb2.ar(
        dry + (delayMix[0] * 0.4),
        dry + (delayMix[1] * 0.4),
        mix: 0.65,
        room: 0.93,
        damp: 0.25
    );

    // === FINAL MIX ===
    out = (dry ! 2 * 0.45) + (delayMix * 0.55) + (verb * 0.65);
    out = out * 0.35;

    // Long fade in/out for breathing room
    out = out * EnvGen.kr(Env([0, 1, 1, 0], [8, dur - 18, 10]));
    out = Limiter.ar(out, 0.95);

    out;
}
