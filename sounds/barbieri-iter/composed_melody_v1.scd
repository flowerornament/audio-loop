// "Ascending Light" - A Composed Melody
//
// This is an actual COMPOSITION, not just cycling patterns
// Structure: A melody with motifs, development, phrases, cadences
//
// Melodic principles:
// - Clear motif (ascending fifth, descending step)
// - Repetition with variation
// - Question and answer phrases
// - Rhythmic variety (not all equal notes)
// - Sense of direction and arrival

{
    var dur, time;
    var maths1, drift1;
    var tempo, clock, phrasePos, melodyNote, rhythmGate;
    var dpoFreq, dpoMod, dpoOsc1, dpoOsc2, dpoMix;
    var harmonics, harmMix;
    var env, lpgFreq, filtered, dry;
    var delay1, delay2, delayMix;
    var verb, out;

    dur = 180;
    time = Line.kr(0, dur, dur);

    // Gentle modulation
    maths1 = LFTri.kr(0.04).range(0, 1);
    drift1 = SinOsc.kr(0.021);

    tempo = 5;
    clock = Impulse.kr(tempo);

    // === THE COMPOSED MELODY ===
    // 32 steps = 2 phrases of 16 (question + answer)
    //
    // PHRASE 1 (Question): Rising gesture, ends suspended
    // Motif A: A-E (fifth up), then step down to D
    // Motif A': Variation - starts higher
    //
    // PHRASE 2 (Answer): Resolving gesture, ends on tonic
    // Motif B: Descending from high E
    // Cadence: Settling back to A

    phrasePos = Stepper.kr(clock, 0, 0, 31);

    melodyNote = Select.kr(phrasePos, [
        // PHRASE 1: Question (bars 1-4)
        // Bar 1: Motif A - ascending fifth
        57, 57, 64, 64,   // A4, A4, E5, E5 (motif: fifth up)
        // Bar 2: Step down, pause
        62, 62, 62, 0,    // D5, D5, D5, rest
        // Bar 3: Motif A' - variation, starts on E
        64, 64, 69, 69,   // E5, E5, A5, A5 (higher)
        // Bar 4: Suspended, awaiting resolution
        67, 67, 64, 64,   // G5, G5, E5, E5

        // PHRASE 2: Answer (bars 5-8)
        // Bar 5: Descent begins
        69, 69, 67, 67,   // A5, A5, G5, G5
        // Bar 6: Continue descent
        64, 64, 62, 62,   // E5, E5, D5, D5
        // Bar 7: Approach home
        60, 60, 62, 64,   // C5, C5, D5, E5 (turn)
        // Bar 8: Cadence - home!
        57, 57, 57, 57    // A4, A4, A4, A4 (rest on tonic)
    ]).midicps;

    // Rhythm: Some notes are held (gate stays high)
    rhythmGate = Select.kr(phrasePos, [
        1, 0, 1, 0,  1, 0, 0, 0,  1, 0, 1, 0,  1, 0, 1, 0,  // Phrase 1
        1, 0, 1, 0,  1, 0, 1, 0,  1, 0, 1, 1,  1, 0, 0, 0   // Phrase 2
    ]);

    // Note: 0 in melody = rest (silent)
    rhythmGate = rhythmGate * (melodyNote > 30);  // Silence rests

    // === DPO ===
    dpoFreq = melodyNote;
    dpoMod = 2.5 + (maths1 * 1.5);

    dpoOsc1 = SinOsc.ar(dpoFreq);
    dpoOsc2 = SinOsc.ar(dpoFreq + (dpoOsc1 * dpoMod * dpoFreq));
    dpoMix = (dpoOsc1 * 0.35) + (dpoOsc2 * 0.65);

    // === HARMONIC OSCILLATOR ===
    harmonics = 8.collect { |i|
        var harmonicNum = i + 1;
        var harmonicFreq = melodyNote * harmonicNum;
        var tilt = drift1 * 0.2;
        var amp = (harmonicNum / 4).pow(tilt) / harmonicNum.pow(0.5);
        SinOsc.ar(harmonicFreq) * amp;
    };
    harmMix = Mix(harmonics);

    filtered = (dpoMix * 0.6) + (harmMix * 0.4);

    // === ENVELOPE ===
    env = EnvGen.ar(
        Env.perc(0.005, 0.55, 1, -4),
        rhythmGate * clock
    );

    lpgFreq = Lag.ar(env, 0.015).linexp(0.001, 1, 600, 10000);
    filtered = RLPF.ar(filtered, lpgFreq, 0.45) * env;

    dry = filtered * 0.45;

    // === EFFECTS ===
    delay1 = CombL.ar(dry, 1, 0.333, 5) * 0.5;
    delay2 = CombL.ar(dry, 1, 0.5, 6) * 0.45;

    delayMix = [delay1, delay2 + (delay1 * 0.4)];

    verb = FreeVerb2.ar(
        dry + (delayMix[0] * 0.35),
        dry + (delayMix[1] * 0.35),
        mix: 0.6,
        room: 0.9,
        damp: 0.25
    );

    out = (dry ! 2 * 0.5) + (delayMix * 0.45) + (verb * 0.55);
    out = out * 0.5;

    out = out * EnvGen.kr(Env([0, 1, 1, 0], [4, dur - 10, 6]));
    out = Limiter.ar(out, 0.95);

    out;
}
