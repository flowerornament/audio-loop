// Caterina Barbieri Full Synth v1
// Harmonic Oscillator + Sequencer + Negative Counterpoint + Effects
//
// Artistic intent: Create hypnotic, meditative patterns that feel alive
// The delay/reverb creates polyphonic depth from a single monophonic voice
// Negative counterpoint reveals hidden melodies within the pattern

{
    // All vars must be declared first in SC
    var tempo, clock, pitchPattern, numSteps, step, baseFreq;
    var gateProb, gate;
    var harmonics, harmMix;
    var env, lpgFreq, lpgQ, filtered, dry;
    var delayTime1, delayTime2, delayTime3, feedback;
    var delayL, delayR, delay2L, delay2R, delayed;
    var verb, out;

    tempo = 5;
    clock = Impulse.kr(tempo);

    // Pitch pattern in higher register - creates that crystalline quality
    pitchPattern = [72, 74, 77, 79, 81, 84, 86, 89, 84, 81, 79, 77, 74, 72, 69, 67];
    numSteps = pitchPattern.size;

    step = Stepper.kr(clock, 0, 0, numSteps - 1);
    baseFreq = Select.kr(step, pitchPattern).midicps;

    // NEGATIVE COUNTERPOINT - the key to her technique
    // Full pattern exists, but gates randomly subtract notes
    // What remains feels discovered, not composed
    gateProb = 0.7;
    gate = TRand.kr(0, 1, clock) < gateProb;

    // === HARMONIC OSCILLATOR ===
    harmonics = 8.collect { |i|
        var harmonicNum = i + 1;
        var harmonicFreq = baseFreq * harmonicNum;
        var amp = 1 / harmonicNum.pow(0.5);
        SinOsc.ar(harmonicFreq) * amp;
    };
    harmMix = Mix(harmonics);

    // === LOW PASS GATE ===
    env = EnvGen.ar(
        Env.perc(0.003, 0.6, 1, -6),
        gate * clock
    );

    lpgFreq = env.linexp(0.001, 1, 400, 12000);
    lpgQ = 0.5;
    filtered = RLPF.ar(harmMix, lpgFreq, lpgQ);
    dry = filtered * env;

    // === EFFECTS - The Space ===
    // Delays create echoing repetitions that blur into polyphony
    delayTime1 = 0.375;
    delayTime2 = 0.25;
    delayTime3 = 0.5;

    delayL = CombL.ar(dry, 1, delayTime1, 3) * 0.4;
    delayR = CombL.ar(dry, 1, delayTime2, 2.5) * 0.4;

    delay2L = CombL.ar(delayR, 1, delayTime3, 4) * 0.3;
    delay2R = CombL.ar(delayL, 1, delayTime3 * 0.75, 3.5) * 0.3;

    delayed = [delayL + delay2L, delayR + delay2R];

    // Large reverb - the vast interior space
    verb = FreeVerb2.ar(
        dry + (delayed[0] * 0.5),
        dry + (delayed[1] * 0.5),
        mix: 0.6,
        room: 0.9,
        damp: 0.4
    );

    out = (dry * 0.5) + (delayed * 0.35) + (verb * 0.5);
    out = out * 0.25;
    out = Limiter.ar(out, 0.95);

    out;
}
