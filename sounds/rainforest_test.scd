// RAINFOREST TEST - 10 second version to validate synthesis

(
// Layer 1: The Earth
SynthDef(\forestFloor, { |out=0|
    var earth = LPF.ar(BrownNoise.ar(0.3), 80);
    var rumble = SinOsc.ar(LFNoise1.kr(0.1).exprange(18, 25), 0, 0.1);
    var sig = Pan2.ar(earth + rumble, LFNoise1.kr(0.03).range(-0.2, 0.2));
    Out.ar(out, sig * 0.7);
}).store;

// Layer 2: Insects
SynthDef(\insects, { |out=0|
    var cicadas = Mix.fill(4, {
        var freq = LFNoise1.kr(0.2).exprange(2800, 4200);
        SinOsc.ar(freq, 0, 0.03) * SinOsc.ar(LFNoise0.kr(0.5).range(4, 12), 0, 0.5, 0.5);
    });
    var crickets = Mix.fill(3, { |i|
        var chirp = Ringz.ar(
            Impulse.ar(LFNoise0.kr(0.3).range(3, 8)) * LFNoise1.kr(2).range(0.3, 1),
            LFNoise1.kr(0.1).exprange(3500, 5500),
            0.02
        );
        Pan2.ar(chirp * 0.06, LFNoise1.kr(0.1).range(-1, 1));
    });
    Out.ar(out, FreeVerb.ar(cicadas + crickets, 0.3, 0.6, 0.3));
}).store;

// Layer 3: Frogs
SynthDef(\frogs, { |out=0|
    var peepers = Mix.fill(3, {
        var trig = Dust.ar(LFNoise0.kr(0.2).range(0.5, 2));
        var call = Ringz.ar(trig, LFNoise0.kr(0.5).exprange(1800, 3200), 0.08) * 0.12;
        Pan2.ar(call, LFNoise1.kr(0.2).range(-1, 1));
    });
    Out.ar(out, FreeVerb.ar(peepers, 0.5, 0.7, 0.4));
}).store;

// Layer 4: Birds
SynthDef(\birds, { |out=0|
    var calls = Mix.fill(3, {
        var trig = Dust.ar(0.3);
        var freq = LFNoise0.kr(0.3).exprange(800, 2400);
        var call = SinOsc.ar(freq * LFNoise1.kr(8).range(0.95, 1.1), 0, 0.12);
        call = call * Decay2.ar(trig, 0.02, 0.2);
        Pan2.ar(call, LFNoise1.kr(0.2).range(-1, 1));
    });
    Out.ar(out, FreeVerb.ar(calls, 0.6, 0.8, 0.5));
}).store;

// Layer 5: Water drips
SynthDef(\water, { |out=0|
    var drips = Mix.fill(5, {
        var trig = Dust.ar(LFNoise0.kr(0.2).range(0.5, 2));
        var drip = Ringz.ar(trig, LFNoise0.kr(0.5).exprange(2000, 5000), 0.01) * 0.08;
        Pan2.ar(drip, LFNoise1.kr(0.3).range(-1, 1));
    });
    var rain = HPF.ar(PinkNoise.ar(0.05), 3000);
    Out.ar(out, drips + Pan2.ar(rain, 0));
}).store;

// Master
SynthDef(\master, { |out=0, in=10|
    var sig = In.ar(in, 2);
    sig = FreeVerb2.ar(sig[0], sig[1], 0.4, 0.85, 0.4);
    sig = Limiter.ar(sig, 0.95);
    Out.ar(out, sig);
}).store;

Score([
    [0.0, [\s_new, \forestFloor, 1000, 0, 1, \out, 10]],
    [0.0, [\s_new, \insects, 1001, 0, 1, \out, 10]],
    [0.0, [\s_new, \frogs, 1002, 0, 1, \out, 10]],
    [0.0, [\s_new, \birds, 1003, 0, 1, \out, 10]],
    [0.0, [\s_new, \water, 1004, 0, 1, \out, 10]],
    [0.0, [\s_new, \master, 2000, 1, 1, \out, 0, \in, 10]],
    [10.0, [\c_set, 0, 0]]
]).recordNRT(
    outputFilePath: "__OUTPUT_PATH__",
    headerFormat: "WAV",
    sampleFormat: "int24",
    sampleRate: 48000,
    options: ServerOptions.new.numOutputBusChannels_(2).numInputBusChannels_(0)
);
)
