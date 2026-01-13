// "Emergence" - Caterina Barbieri Style Composition
// Using accurate modular recreation
//
// Structure: 2 minutes of gradual pattern revelation
// Sparse opening → building density → release

{
    var dur = 120;
    var time = Line.kr(0, dur, dur);

    // Global evolution envelope
    var evolution = EnvGen.kr(
        Env([0.2, 0.4, 0.85, 0.7, 0.3], [25, 35, 35, 25]),
        timeScale: 1
    );

    var tempo, clock, pitchPattern, numSteps, step, baseFreq;
    var gateProb, gate;
    var wobble, woggleStepped, woggleSmooth;
    var dpoFreq1, dpoFreq2, dpoMod, dpoOsc1, dpoOsc2, dpoMix;
    var harmonics, tiltMod, scanMod, harmMix;
    var oscMix, env, lpgFreq, filtered, dry;
    var echoShift, pitchShiftedL, pitchShiftedR;
    var verb, out;

    tempo = 4.5 + (SinOsc.kr(0.02) * 0.3);  // Slight tempo drift
    clock = Impulse.kr(tempo);

    // Wogglebug modulation
    woggleStepped = LFNoise0.kr(0.4);
    woggleSmooth = LFNoise2.kr(0.15);
    wobble = LFNoise1.kr(1.5);

    // ER-101 Pattern - limited pitch set for minimalist feel
    pitchPattern = [60, 62, 65, 67, 69, 72, 74, 77, 72, 69, 67, 65, 62, 60, 58, 60];
    numSteps = pitchPattern.size;
    step = Stepper.kr(clock, 0, 0, numSteps - 1);
    baseFreq = Select.kr(step, pitchPattern).midicps;

    // Negative counterpoint - density follows evolution
    gateProb = 0.3 + (evolution * 0.55) + (woggleSmooth * 0.1);
    gate = TRand.kr(0, 1, clock) < gateProb;

    // === DPO ===
    dpoFreq1 = baseFreq;
    dpoFreq2 = baseFreq * (1 + (woggleStepped * 0.015));
    dpoMod = wobble.range(0.3, 2.5) * evolution;

    dpoOsc1 = SinOsc.ar(dpoFreq1);
    dpoOsc2 = SinOsc.ar(dpoFreq2 + (dpoOsc1 * dpoMod * dpoFreq2 * 0.5));
    dpoMix = (dpoOsc1 * 0.5) + (dpoOsc2 * 0.5);

    // === HARMONIC OSCILLATOR ===
    tiltMod = SinOsc.kr(0.05).range(-0.4, 0.4);
    scanMod = SinOsc.kr(0.08).range(2, 6);

    harmonics = 8.collect { |i|
        var harmonicNum = i + 1;
        var harmonicFreq = baseFreq * harmonicNum;
        var tiltFactor = (harmonicNum / 4.5).pow(tiltMod);
        var distance = (harmonicNum - scanMod).abs;
        var scanFactor = (1 - (distance / 4)).max(0);
        var amp = tiltFactor * scanFactor / harmonicNum.pow(0.6);
        SinOsc.ar(harmonicFreq) * amp;
    };
    harmMix = Mix(harmonics);

    // Mix oscillators
    oscMix = (dpoMix * 0.4) + (harmMix * 0.6);

    // === MATHS ENVELOPE + OPTOMIX LPG ===
    env = EnvGen.ar(
        Env.perc(0.004, 0.5 + (woggleSmooth * 0.2), 1, -5),
        gate * clock
    );

    lpgFreq = Lag.ar(env, 0.015).linexp(0.001, 1, 400, 10000);
    filtered = RLPF.ar(oscMix, lpgFreq, 0.55) * env;
    dry = filtered;

    // === ECHOPHON - Pitch Shifting Delay ===
    echoShift = 7;  // Perfect fifth up
    pitchShiftedL = PitchShift.ar(
        CombL.ar(dry, 1, 0.375, 3),
        windowSize: 0.08,
        pitchRatio: echoShift.midiratio,
        pitchDispersion: 0.005,
        timeDispersion: 0.005
    ) * 0.4;

    pitchShiftedR = PitchShift.ar(
        CombL.ar(dry, 1, 0.25, 2.5),
        windowSize: 0.08,
        pitchRatio: (echoShift + 4).midiratio,  // Major third above the fifth
        pitchDispersion: 0.005,
        timeDispersion: 0.005
    ) * 0.35;

    // === ERBE-VERB ===
    verb = FreeVerb2.ar(
        dry + pitchShiftedL,
        dry + pitchShiftedR,
        mix: 0.55,
        room: 0.9,
        damp: 0.3
    );

    // Final mix - LOUDER
    out = (dry ! 2 * 0.6) + ([pitchShiftedL, pitchShiftedR] * 0.5) + (verb * 0.6);
    out = out * 0.5;  // Boost overall

    // Fade in/out
    out = out * EnvGen.kr(Env([0, 1, 1, 0], [4, dur - 10, 6]));
    out = Limiter.ar(out, 0.95);

    out;
}
