{
// XTAL: simple, bright, shimmery, space
var dur = 10;
var masterEnv = Line.ar(1, 1, dur, doneAction: Done.freeSelf);

// === SHIMMERY PAD: bright, detuned, in the mids ===
var padNote = 60;  // Middle C
var padFreqs = [0, 7, 12, 16].collect { |i| (padNote + i).midicps };  // C major add9
var pad = Mix(padFreqs.collect { |f|
    var fundamental = SinOsc.ar(f * 0.998) + SinOsc.ar(f * 1.002) + SinOsc.ar(f * 1.0);
    var harmonics = (SinOsc.ar(f * 2.001) * 0.4) + (SinOsc.ar(f * 3.002) * 0.15);
    (fundamental + harmonics) * 0.08
});
var padFiltered = LPF.ar(pad, 3500 + (SinOsc.kr(0.08) * 800));
var padL = padFiltered;
var padR = DelayN.ar(padFiltered, 0.03, 0.012);

// === SIMPLE MELODY: naive, emotional, repeating ===
var melTrig = Impulse.ar(1.6);
var melNotes = [72, 72, 74, 72, 71, 67, 72, 71];
var melFreq = Demand.ar(melTrig, 0, Dseq(melNotes.midicps, inf));
var melEnv = EnvGen.ar(Env.perc(0.01, 0.8, 1, -4), melTrig);
var melody = (SinOsc.ar(melFreq) + (SinOsc.ar(melFreq * 2.002) * 0.3)) * melEnv * 0.2;
var melodyL = melody * 0.7;
var melodyR = DelayN.ar(melody, 0.05, 0.02) * 0.7;

// === SOFT KICK: felt not heard ===
var kickTrig = Impulse.ar(1.6);
var kickEnv = EnvGen.ar(Env.perc(0.01, 0.3), kickTrig);
var kick = SinOsc.ar(EnvGen.ar(Env([80, 80, 45], [0, 0.1], \exp), kickTrig)) * kickEnv * 0.25;

// === SOFT BASS: gentle low end ===
var bassFreq = padNote.midicps / 2;
var bass = SinOsc.ar(bassFreq) * 0.15 * (1 + (SinOsc.kr(0.1) * 0.1));

// === SPACE: reverb tail ===
var verbIn = melody * 0.4;
var combTimes = [0.031, 0.037, 0.043, 0.053];
var verb = Mix.fill(4, { |i| CombL.ar(verbIn, 0.1, combTimes[i], 3) * 0.12 });
var verbL = verb;
var verbR = DelayN.ar(verb, 0.05, 0.015);

// === FINAL MIX ===
var mixL = padL + melodyL + kick + bass + verbL;
var mixR = padR + melodyR + kick + bass + verbR;
var outL = (mixL * 1.2).tanh * 0.75;
var outR = (mixR * 1.2).tanh * 0.75;

[outL, outR] * masterEnv;
}
