// Caterina Barbieri - Inspired Composition v1
// "Patterns of Emergence"
//
// A meditation on pattern and subtraction.
// The full melodic potential exists from the start,
// but only fragments are revealed through the gates.
// Over time, the pattern becomes more complete,
// then recedes again.
//
// Duration: ~90 seconds
// Structure: Sparse → Dense → Sparse

{
    var dur = 90;
    var time = Line.kr(0, dur, dur);

    // Time-based modulation - the arc of the piece
    var density = EnvGen.kr(
        Env([0.3, 0.5, 0.9, 0.75, 0.4], [20, 25, 25, 20]),
        timeScale: 1
    );

    var tempo, clock, pitchPatternHigh, pitchPatternLow;
    var numStepsHigh, stepHigh, freqHigh;
    var numStepsLow, stepLow, freqLow;
    var gateHigh, gateLow;
    var harmonicsHigh, harmMixHigh, harmonicsLow, harmMixLow;
    var envHigh, envLow, lpgFreqHigh, lpgFreqLow;
    var filteredHigh, filteredLow, dryHigh, dryLow, dry;
    var delayL, delayR, delay2L, delay2R, delayed;
    var verb, out;

    tempo = 4.5;
    clock = Impulse.kr(tempo);

    // === HIGH VOICE - Crystalline arpeggios ===
    pitchPatternHigh = [72, 74, 77, 79, 81, 84, 86, 89, 91, 84, 81, 79, 77, 74];
    numStepsHigh = pitchPatternHigh.size;
    stepHigh = Stepper.kr(clock, 0, 0, numStepsHigh - 1);
    freqHigh = Select.kr(stepHigh, pitchPatternHigh).midicps;

    // Negative counterpoint - more notes revealed over time
    gateHigh = TRand.kr(0, 1, clock) < density;

    // 8 harmonics with slight spectral motion
    harmonicsHigh = 8.collect { |i|
        var harmonicNum = i + 1;
        var harmonicFreq = freqHigh * harmonicNum;
        var tilt = SinOsc.kr(0.03, 0, 0.3, 0.5).pow(harmonicNum / 5);
        var amp = tilt / harmonicNum.pow(0.6);
        SinOsc.ar(harmonicFreq) * amp;
    };
    harmMixHigh = Mix(harmonicsHigh);

    envHigh = EnvGen.ar(
        Env.perc(0.003, 0.5 + (density * 0.3), 1, -5),
        gateHigh * clock
    );
    lpgFreqHigh = envHigh.linexp(0.001, 1, 600, 10000);
    filteredHigh = RLPF.ar(harmMixHigh, lpgFreqHigh, 0.6);
    dryHigh = filteredHigh * envHigh * 0.45;

    // === LOW VOICE - Bass drone (for the low-end presence) ===
    pitchPatternLow = [36, 36, 41, 36, 43, 36, 41, 36]; // Pedal tone with movement
    numStepsLow = pitchPatternLow.size;
    stepLow = Stepper.kr(Impulse.kr(tempo * 0.25), 0, 0, numStepsLow - 1);
    freqLow = Select.kr(stepLow, pitchPatternLow).midicps;

    gateLow = TRand.kr(0, 1, Impulse.kr(tempo * 0.25)) < (density * 0.8);

    harmonicsLow = 4.collect { |i|
        var harmonicNum = i + 1;
        var harmonicFreq = freqLow * harmonicNum;
        var amp = 1 / harmonicNum.pow(1.2);
        SinOsc.ar(harmonicFreq) * amp;
    };
    harmMixLow = Mix(harmonicsLow);

    envLow = EnvGen.ar(
        Env.perc(0.01, 1.5, 1, -3),
        gateLow * Impulse.kr(tempo * 0.25)
    );
    lpgFreqLow = envLow.linexp(0.001, 1, 100, 800);
    filteredLow = LPF.ar(harmMixLow, lpgFreqLow);
    dryLow = filteredLow * envLow * 0.35;

    // Combine voices
    dry = dryHigh + dryLow;

    // === EFFECTS ===
    delayL = CombL.ar(dry, 1, 0.375, 3.5) * 0.35;
    delayR = CombL.ar(dry, 1, 0.25, 3) * 0.35;
    delay2L = CombL.ar(delayR, 1, 0.5, 4.5) * 0.25;
    delay2R = CombL.ar(delayL, 1, 0.333, 4) * 0.25;
    delayed = [delayL + delay2L, delayR + delay2R];

    verb = FreeVerb2.ar(
        dry + (delayed[0] * 0.4),
        dry + (delayed[1] * 0.4),
        mix: 0.55,
        room: 0.92,
        damp: 0.35
    );

    // Final mix with gentle fade in/out
    out = (dry * 0.4) + (delayed * 0.3) + (verb * 0.55);
    out = out * 0.22;
    out = out * EnvGen.kr(Env([0, 1, 1, 0], [3, dur - 7, 4]));
    out = Limiter.ar(out, 0.95);

    out;
}
