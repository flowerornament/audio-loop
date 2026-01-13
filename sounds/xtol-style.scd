{
// XTAL-style: warm ambient, sustained pads, sub bass, smooth
var dur = 10;
var masterEnv = Line.ar(1, 1, dur, doneAction: Done.freeSelf);

// === SUB BASS: continuous low drone with subtle movement ===
var subFreq = 42;  // Low F
var sub = SinOsc.ar(subFreq) * 0.4 * (1 + (SinOsc.kr(0.15) * 0.1));

// === WARM PAD: detuned saws filtered down, stereo spread ===
var padFreqs = [48, 55, 60, 64].midicps;  // C minor-ish chord
var padL = Mix(padFreqs.collect { |f, i|
    var sig = LFSaw.ar(f * 0.997) + LFSaw.ar(f * 0.998) + LFSaw.ar(f * 1.002);
    LPF.ar(sig, 800 + (SinOsc.kr(0.1 + (i * 0.02)) * 200)) * 0.08
});
var padR = Mix(padFreqs.collect { |f, i|
    var sig = LFSaw.ar(f * 1.003) + LFSaw.ar(f * 1.004) + LFSaw.ar(f * 0.996);
    LPF.ar(sig, 850 + (SinOsc.kr(0.12 + (i * 0.02)) * 200)) * 0.08
});

// === GENTLE KICK: soft 4/4, more sub than click ===
var kickTrig = Impulse.ar(2);  // quarter notes at 120bpm-ish
var kickEnv = EnvGen.ar(Env.perc(0.01, 0.4), kickTrig);
var kick = SinOsc.ar(EnvGen.ar(Env([55, 55, 38], [0, 0.15], \exp), kickTrig)) * kickEnv * 0.35;

// === MELODIC LEAD: simple sine melody with long release ===
var melodyTrig = Impulse.ar(0.8);  // slow arpeggiation
var melNotes = [72, 67, 64, 60, 67, 72, 76, 72];  // C minor descent/ascent
var melFreq = Demand.ar(melodyTrig, 0, Dseq(melNotes.midicps, inf));
var melEnv = EnvGen.ar(Env.perc(0.05, 1.5), melodyTrig);
var melodyL = ((SinOsc.ar(melFreq * 0.999) * 0.2) + (SinOsc.ar(melFreq * 2.001 * 0.999) * 0.06)) * melEnv;
var melodyR = ((SinOsc.ar(melFreq * 1.001) * 0.2) + (SinOsc.ar(melFreq * 2.001 * 1.001) * 0.06)) * melEnv;

// === TEXTURE: filtered noise bed for air/space ===
var noiseL = LPF.ar(HPF.ar(PinkNoise.ar, 200), 2000) * 0.03;
var noiseR = LPF.ar(HPF.ar(PinkNoise.ar, 200), 2200) * 0.03;

// === SIMPLE REVERB via comb filters ===
var reverbIn = (melodyL + melodyR) * 0.3;
var combTimes = [0.037, 0.043, 0.051, 0.059];
var verb = Mix.fill(4, { |i|
    CombL.ar(reverbIn, 0.1, combTimes[i], 2.5) * 0.15
});
var verbL = verb * (0.7 + (LFNoise1.kr(0.5).range(0.0, 0.3)));
var verbR = verb * (0.7 + (LFNoise1.kr(0.6).range(0.0, 0.3)));

// === FINAL MIX with soft saturation ===
var mixL = sub + padL + kick + melodyL + noiseL + verbL;
var mixR = sub + padR + kick + melodyR + noiseR + verbR;
var outL = (mixL * 1.5).tanh * 0.7;
var outR = (mixR * 1.5).tanh * 0.7;

[outL, outR] * masterEnv;
}
