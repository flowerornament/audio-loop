// Caterina Barbieri Full Rig v2
// Accurate recreation based on actual ModularGrid setup
//
// OSCILLATORS:
// - DPO (Dual Primary Oscillator) - FM complex oscillator
// - Verbos Harmonic Oscillator - additive 8 harmonics
//
// MODULATION:
// - Maths - function generators
// - Wogglebug - random modulation source
//
// GATES/VCAs:
// - Optomix - low pass gates with vactrol character
//
// EFFECTS:
// - Echophon - PITCH-SHIFTING delay (key!)
// - Erbe-Verb - metallic/ambient reverb

{
    var dur = 60;
    var tempo, clock, pitchPattern, numSteps, step, baseFreq;
    var gateProb, gate;

    // Wogglebug-style random modulation
    var wobble, woggleRate, woggleStepped, woggleSmooth;

    // DPO oscillator (dual complex with FM)
    var dpoFreq1, dpoFreq2, dpoMod, dpoOsc1, dpoOsc2, dpoMix;

    // Harmonic oscillator
    var harmonics, tiltMod, scanMod, harmMix;

    // Combined oscillators
    var oscMix;

    // Maths-style envelope
    var rise, fall, envCurve, env;

    // LPG (Optomix)
    var lpgFreq, lpgRing, filtered;

    // Echophon (pitch-shifting delay)
    var echoShift, echoTime, echoFeedback, echoWet;
    var pitchShiftedL, pitchShiftedR;

    // Erbe-Verb
    var verbMix, verbDecay, verb;

    var dry, out;

    tempo = 4;
    clock = Impulse.kr(tempo);

    // === WOGGLEBUG - Random modulation ===
    woggleRate = 0.5;
    woggleStepped = LFNoise0.kr(woggleRate);  // Stepped random
    woggleSmooth = LFNoise2.kr(woggleRate * 0.3);  // Smooth random
    wobble = LFNoise1.kr(2);  // Medium wander

    // === SEQUENCER (ER-101 style) ===
    pitchPattern = [60, 62, 65, 67, 69, 72, 67, 65, 74, 72, 69, 67, 65, 62, 60, 58];
    numSteps = pitchPattern.size;
    step = Stepper.kr(clock, 0, 0, numSteps - 1);
    baseFreq = Select.kr(step, pitchPattern).midicps;

    // Negative counterpoint - gate probability modulated by wogglebug
    gateProb = 0.65 + (woggleSmooth * 0.2);
    gate = TRand.kr(0, 1, clock) < gateProb;

    // === DPO - DUAL PRIMARY OSCILLATOR ===
    // Two oscillators with cross-FM
    dpoFreq1 = baseFreq;
    dpoFreq2 = baseFreq * (1 + (woggleStepped * 0.02));  // Slight detune from wogglebug

    // FM modulation amount varies with wobble
    dpoMod = wobble.range(0.5, 3);

    // Osc1 modulates Osc2 (complex FM)
    dpoOsc1 = SinOsc.ar(dpoFreq1);
    dpoOsc2 = SinOsc.ar(dpoFreq2 + (dpoOsc1 * dpoMod * dpoFreq2));

    // Mix of both oscillators
    dpoMix = (dpoOsc1 * 0.4) + (dpoOsc2 * 0.6);

    // === VERBOS HARMONIC OSCILLATOR ===
    // Slow spectral modulation
    tiltMod = SinOsc.kr(0.07).range(-0.5, 0.5);
    scanMod = SinOsc.kr(0.11).range(2, 6);

    harmonics = 8.collect { |i|
        var harmonicNum = i + 1;
        var harmonicFreq = baseFreq * harmonicNum;
        // Apply tilt
        var tiltFactor = (harmonicNum / 4.5).pow(tiltMod);
        // Apply scan (bandpass-like)
        var distance = (harmonicNum - scanMod).abs;
        var scanFactor = (1 - (distance / 4)).max(0);
        var amp = tiltFactor * scanFactor / harmonicNum.pow(0.7);
        SinOsc.ar(harmonicFreq) * amp;
    };
    harmMix = Mix(harmonics);

    // === COMBINE OSCILLATORS ===
    oscMix = (dpoMix * 0.5) + (harmMix * 0.5);

    // === MATHS - Envelope Generator ===
    rise = 0.005;
    fall = 0.4 + (woggleSmooth * 0.2);  // Decay varies with modulation
    envCurve = -5;

    env = EnvGen.ar(
        Env.perc(rise, fall, 1, envCurve),
        gate * clock
    );

    // === OPTOMIX - Low Pass Gate ===
    // Vactrol character: filter tracks amplitude with slight lag
    lpgRing = 0.02;  // Vactrol "ring" time
    lpgFreq = Lag.ar(env, lpgRing).linexp(0.001, 1, 300, 8000);

    filtered = RLPF.ar(oscMix, lpgFreq, 0.5) * env;

    dry = filtered * 0.4;

    // === ECHOPHON - Pitch Shifting Delay ===
    // This is KEY to her sound - delays that transpose
    echoShift = 7;  // Shift up a fifth (7 semitones)
    echoTime = 0.333;  // Dotted quarter feel
    echoFeedback = 0.45;

    // Pitch shift the delayed signal
    pitchShiftedL = PitchShift.ar(
        CombL.ar(dry, 1, echoTime, 2.5),
        windowSize: 0.1,
        pitchRatio: echoShift.midiratio,
        pitchDispersion: 0.01,
        timeDispersion: 0.01
    ) * 0.35;

    pitchShiftedR = PitchShift.ar(
        CombL.ar(dry, 1, echoTime * 0.75, 2),
        windowSize: 0.1,
        pitchRatio: (echoShift + 5).midiratio,  // Shift up a major third further
        pitchDispersion: 0.01,
        timeDispersion: 0.01
    ) * 0.3;

    // === ERBE-VERB ===
    verb = FreeVerb2.ar(
        dry + pitchShiftedL,
        dry + pitchShiftedR,
        mix: 0.6,
        room: 0.88,
        damp: 0.3
    );

    // Final mix
    out = (dry ! 2 * 0.5) + ([pitchShiftedL, pitchShiftedR] * 0.4) + (verb * 0.5);
    out = out * 0.25;
    out = Limiter.ar(out, 0.95);

    out;
}
