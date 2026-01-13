// "Radiant Cycles" - Bright, Fast, DPO-forward
//
// Feedback: More repetitive, faster, brighter, hear the DPO!
// The DPO creates rich harmonics through FM - almost sawtooth-like
// Higher tempo, simpler pattern, brighter filter, more modulation

{
    var dur, time;
    var maths1, maths2;
    var woggleStepped, woggleSmooth;
    var drift1, drift2;
    var tempo, clock, step, baseFreq, gate, gateProb;
    var dpoFreq, dpoMod, dpoOsc1, dpoOsc2, dpoMix;
    var harmonics, harmMix;
    var env, lpgFreq, filtered, dry;
    var delay1, delay2, delay3, delayMix;
    var verb, out;

    dur = 180;
    time = Line.kr(0, dur, dur);

    // Modulation sources
    maths1 = LFTri.kr(0.05).range(0, 1);
    maths2 = LFTri.kr(0.12).range(0, 1);
    woggleStepped = LFNoise0.kr(0.4);
    woggleSmooth = LFNoise2.kr(0.2);
    drift1 = SinOsc.kr(0.019);
    drift2 = SinOsc.kr(0.027);

    // FASTER tempo
    tempo = 6;  // Was 4.5
    clock = Impulse.kr(tempo);

    // SIMPLE, REPETITIVE pattern - just 4 notes cycling
    // A minor: A, C, E, A (octave)
    step = Stepper.kr(clock, 0, 0, 7);
    baseFreq = Select.kr(step, [
        69, 72, 76, 81,  // A4, C5, E5, A5
        69, 72, 76, 81   // Repeat exactly - hypnotic!
    ]).midicps;

    // High gate probability - continuous flow
    gateProb = 0.88;
    gate = TRand.kr(0, 1, clock) < gateProb;

    // === DPO - PROMINENT, BRIGHT ===
    // Higher modulation index = richer harmonics (sawtooth-like)
    dpoFreq = baseFreq;
    dpoMod = 3 + (maths2 * 2) + (woggleSmooth * 0.5);  // Higher FM index!

    dpoOsc1 = SinOsc.ar(dpoFreq);
    // Strong FM creates saw-like harmonics
    dpoOsc2 = SinOsc.ar(dpoFreq + (dpoOsc1 * dpoMod * dpoFreq));

    // Mix with emphasis on modulated oscillator
    dpoMix = (dpoOsc1 * 0.3) + (dpoOsc2 * 0.7);

    // === HARMONIC OSCILLATOR (brighter) ===
    harmonics = 8.collect { |i|
        var harmonicNum = i + 1;
        var harmonicFreq = baseFreq * harmonicNum;
        // LESS rolloff = more brightness
        var amp = 1 / harmonicNum.pow(0.4);  // Was 0.65
        SinOsc.ar(harmonicFreq) * amp;
    };
    harmMix = Mix(harmonics);

    // === MIX OSCILLATORS - DPO forward ===
    // DPO is the star
    filtered = (dpoMix * 0.65) + (harmMix * 0.35);

    // === LPG - BRIGHTER ===
    env = EnvGen.ar(
        Env.perc(0.004, 0.5 + (maths1 * 0.3), 1, -4),
        gate * clock
    );

    // Higher LPG frequencies = brighter
    lpgFreq = Lag.ar(env, 0.012).linexp(0.001, 1, 800, 12000);  // Was 300-6000

    filtered = RLPF.ar(filtered, lpgFreq, 0.4 + (drift1 * 0.1)) * env;

    dry = filtered * 0.5;  // Louder dry signal

    // === DELAY NETWORK ===
    delay1 = CombL.ar(dry, 1, 0.25, 4) * 0.5;
    delay2 = CombL.ar(dry, 1, 0.375, 5) * 0.45;
    delay3 = CombL.ar(dry, 1, 0.167, 3.5) * 0.4;  // Faster delay

    delayMix = [
        delay1 + (delay3 * 0.5),
        delay2 + (delay1 * 0.4)
    ];

    // === REVERB ===
    verb = FreeVerb2.ar(
        dry + (delayMix[0] * 0.4),
        dry + (delayMix[1] * 0.4),
        mix: 0.55,
        room: 0.88,
        damp: 0.2  // Less damping = brighter tail
    );

    // === OUTPUT - LOUDER ===
    out = (dry ! 2 * 0.5) + (delayMix * 0.5) + (verb * 0.55);
    out = out * 0.55;  // Boost!

    out = out * EnvGen.kr(Env([0, 1, 1, 0], [4, dur - 10, 6]));
    out = Limiter.ar(out, 0.95);

    out;
}
