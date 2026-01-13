// "Hypnotic Cycles" - Barbieri Style
// Key insight: Her music is REPETITIVE and CONTINUOUS, not random and plucky
// The delay creates a wash where everything blends together
// Two oscillators with separate roles, evolving slowly

{
    var dur = 120;
    var time = Line.kr(0, dur, dur);

    // Very slow evolution - glacial changes
    var breathe = SinOsc.kr(0.02).range(0.7, 1);
    var drift = SinOsc.kr(0.015, 0, 0.5);

    var tempo, clock;
    var step, baseFreq;
    var gate, gateProb;

    // Oscillator 1 - Harmonic (main voice)
    var harm1Harmonics, harm1Mix, harm1Env, harm1Filtered;

    // Oscillator 2 - DPO style (undertone/texture)
    var dpoFreq, dpoOsc, dpo2Osc, dpoMix, dpoEnv, dpoFiltered;

    // Effects
    var dry, delay1, delay2, delay3, delayMix;
    var verb, out;

    tempo = 5;
    clock = Impulse.kr(tempo);

    // VERY REPETITIVE pattern - limited pitch set, cycling
    // A minor pentatonic, staying close to home
    step = Stepper.kr(clock, 0, 0, 7);
    baseFreq = Select.kr(step, [
        57, 60, 62, 64,  // A, C, D, E
        57, 60, 62, 64   // Repeat exactly - hypnotic!
    ]).midicps;

    // HIGH gate probability - continuous flow, not sparse
    gateProb = 0.92;  // Almost all notes play
    gate = TRand.kr(0, 1, clock) < gateProb;

    // === OSCILLATOR 1: Harmonic (melodic voice) ===
    harm1Harmonics = 8.collect { |i|
        var harmonicNum = i + 1;
        var harmonicFreq = baseFreq * harmonicNum;
        // Slow tilt modulation
        var tilt = drift.range(-0.3, 0.3);
        var amp = (harmonicNum / 4.5).pow(tilt) / harmonicNum.pow(0.7);
        SinOsc.ar(harmonicFreq) * amp;
    };
    harm1Mix = Mix(harm1Harmonics);

    // LONG envelope - notes blend into each other
    harm1Env = EnvGen.ar(
        Env.perc(0.008, 0.8, 1, -4),  // 800ms decay!
        gate * clock
    );

    harm1Filtered = LPF.ar(harm1Mix, harm1Env.linexp(0.001, 1, 500, 6000)) * harm1Env * 0.4;

    // === OSCILLATOR 2: DPO (lower, textural) ===
    // Plays at slower rate, provides foundation
    dpoFreq = Select.kr(
        Stepper.kr(Impulse.kr(tempo * 0.5), 0, 0, 3),
        [45, 45, 48, 45]  // A2, A2, C3, A2 - drone-like
    ).midicps;

    dpoOsc = SinOsc.ar(dpoFreq);
    dpo2Osc = SinOsc.ar(dpoFreq * 2.01);  // Slight detune for beating
    dpoMix = (dpoOsc * 0.7) + (dpo2Osc * 0.3);

    dpoEnv = EnvGen.ar(
        Env.perc(0.02, 1.5, 1, -3),  // Even longer decay
        Impulse.kr(tempo * 0.5) * (TRand.kr(0, 1, Impulse.kr(tempo * 0.5)) < 0.8)
    );

    dpoFiltered = LPF.ar(dpoMix, 800) * dpoEnv * 0.35;

    // === COMBINE DRY ===
    dry = harm1Filtered + dpoFiltered;

    // === MASSIVE DELAY WASH ===
    // Multiple delay times for dense texture
    delay1 = CombL.ar(dry, 2, 0.333, 5) * 0.5;   // Long feedback
    delay2 = CombL.ar(dry, 2, 0.5, 6) * 0.45;
    delay3 = CombL.ar(dry, 2, 0.25, 4.5) * 0.4;

    // Ping-pong spread
    delayMix = [
        delay1 + (delay3 * 0.7),
        delay2 + (delay1 * 0.6)
    ];

    // === HUGE REVERB ===
    verb = FreeVerb2.ar(
        dry + (delayMix[0] * 0.5),
        dry + (delayMix[1] * 0.5),
        mix: 0.7,    // Wet!
        room: 0.95,  // Huge space
        damp: 0.25   // Bright tail
    );

    // Final mix - lots of effect, moderate dry
    out = (dry ! 2 * 0.4) + (delayMix * 0.6) + (verb * 0.7);
    out = out * 0.35 * breathe;

    // Gentle fade
    out = out * EnvGen.kr(Env([0, 1, 1, 0], [5, dur - 12, 7]));
    out = Limiter.ar(out, 0.95);

    out;
}
