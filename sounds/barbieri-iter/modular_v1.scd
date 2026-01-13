// "Woven Threads" - True Modular Patch
// Key insight: EVERYTHING is modulated by SOMETHING

{
    // ALL VARIABLES DECLARED FIRST
    var dur, time;
    var maths1, maths2Rate, maths2;
    var woggleRate, woggleStepped, woggleSmooth;
    var drift1, drift2, drift3;
    var tempo, clock, step, baseFreq, rootNote, gate, gateProb;
    var tiltMod, scanMod, harmonics, harmMix;
    var dpoFreq, dpoDetune, dpoMod, dpoOsc1, dpoOsc2, dpoMix;
    var envAttack, envDecay, env, lpgFreq, filtered, dry;
    var delayTime1, delayTime2, delay1, delay2, delayMix;
    var verb, out;

    dur = 180;
    time = Line.kr(0, dur, dur);

    // === MODULATION SOURCES ===
    maths1 = LFTri.kr(0.04).range(0, 1);
    maths2Rate = maths1.linlin(0, 1, 0.1, 0.5);
    maths2 = LFTri.kr(maths2Rate).range(0, 1);

    woggleRate = 0.3 + (maths1 * 0.2);
    woggleStepped = LFNoise0.kr(woggleRate);
    woggleSmooth = LFNoise2.kr(woggleRate * 0.5);

    drift1 = SinOsc.kr(0.017);
    drift2 = SinOsc.kr(0.023);
    drift3 = SinOsc.kr(0.031);

    // === SEQUENCER ===
    tempo = 4.5 + (maths2 * 0.3);
    clock = Impulse.kr(tempo);

    rootNote = Select.kr((time / 45).floor % 4, [57, 60, 55, 57]);

    step = Stepper.kr(clock, 0, 0, 15);
    baseFreq = (rootNote + Select.kr(step, [
        0, 7, 12, 7, 0, 5, 7, 12, 7, 5, 0, -5, 0, 7, 12, 7
    ]) + (woggleStepped * 2).round).midicps;

    gateProb = 0.6 + (maths1 * 0.35);
    gate = TRand.kr(0, 1, clock) < gateProb;

    // === HARMONIC OSCILLATOR ===
    tiltMod = (drift1 * 0.3) + (maths1 * 0.2);
    scanMod = 4 + (drift2 * 1.5) + (woggleSmooth * 0.5);

    harmonics = 8.collect { |i|
        var harmonicNum = i + 1;
        var harmonicFreq = baseFreq * harmonicNum;
        var tiltFactor = (harmonicNum / 4.5).pow(tiltMod);
        var distance = (harmonicNum - scanMod).abs;
        var scanFactor = (1 - (distance / 3.5)).max(0);
        var amp = tiltFactor * scanFactor / harmonicNum.pow(0.65);
        SinOsc.ar(harmonicFreq) * amp;
    };
    harmMix = Mix(harmonics);

    // === DPO ===
    dpoFreq = baseFreq * 0.5;
    dpoDetune = 1 + (woggleStepped * 0.008);
    dpoMod = maths2.linlin(0, 1, 0.2, 1.5);

    dpoOsc1 = SinOsc.ar(dpoFreq);
    dpoOsc2 = SinOsc.ar(dpoFreq * dpoDetune + (dpoOsc1 * dpoMod * dpoFreq * 0.5));
    dpoMix = (dpoOsc1 + dpoOsc2) * 0.5;

    // === LPG ===
    envAttack = 0.003 + (maths1 * 0.007);
    envDecay = 0.4 + (maths1 * 0.4) + (woggleSmooth * 0.1);

    env = EnvGen.ar(
        Env.perc(envAttack, envDecay, 1, -4 - (drift3 * 2)),
        gate * clock
    );

    lpgFreq = Lag.ar(env, 0.015 + (maths1 * 0.01)).linexp(
        0.001, 1,
        300 + (drift1 * 100),
        6000 + (maths2 * 2000)
    );

    filtered = RLPF.ar(
        (harmMix * 0.5) + (dpoMix * 0.5),
        lpgFreq,
        0.5 + (drift2 * 0.15)
    ) * env;

    dry = filtered * 0.4;

    // === DELAY NETWORK ===
    delayTime1 = 0.333 + (drift1 * 0.01);
    delayTime2 = 0.5 + (drift2 * 0.015);

    delay1 = CombL.ar(dry, 2, delayTime1, 5 + (maths1 * 2)) * 0.5;
    delay2 = CombL.ar(dry, 2, delayTime2, 6 + (maths2 * 1.5)) * 0.45;

    delayMix = [delay1, delay2];

    // === REVERB ===
    verb = FreeVerb2.ar(
        dry + (delayMix[0] * 0.4),
        dry + (delayMix[1] * 0.4),
        mix: 0.6 + (maths1 * 0.1),
        room: 0.92,
        damp: 0.25 + (drift3 * 0.1)
    );

    // === OUTPUT ===
    out = (dry ! 2 * 0.4) + (delayMix * 0.5) + (verb * 0.6);
    out = out * 0.35;
    out = out * EnvGen.kr(Env([0, 1, 1, 0], [6, dur - 14, 8]));
    out = Limiter.ar(out, 0.95);

    out;
}
