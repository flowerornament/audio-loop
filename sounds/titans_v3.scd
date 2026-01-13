// TITANS v3
// Proper SC architecture - add/remove synths freely
// Run blocks in order: Boot -> SynthDefs -> Buses -> Synths

// ==================== 1. BOOT ====================
s.boot;

// ==================== 2. SYNTHDEFS ====================
(
// Master breath - global control
SynthDef(\titans_breath, { |out=0, rate=0.012, min=0.7, max=1|
    var breath = SinOsc.kr(rate).range(min, max);
    Out.kr(out, breath);
}).add;

// Subterranean - the deep
SynthDef(\titans_sub, { |out=0, subOut=0, amp=1, breathBus=0|
    var plates, magma, pressure, vents;
    var breath = In.kr(breathBus);
    var subContent, midContent, sig;

    plates = Mix.fill(4, {
        var freq = LFNoise1.kr(0.01).exprange(8, 25);
        SinOsc.ar(freq, 0, LFNoise1.kr(0.02).range(0.15, 0.4));
    });

    magma = LPF.ar(BrownNoise.ar(0.5), LFNoise1.kr(0.008).exprange(20, 70));

    pressure = SinOsc.ar(
        LFNoise1.kr(0.003).exprange(12, 35),
        0,
        LFNoise1.kr(0.01).range(0, 1).lag(4)
    ) * 0.5;

    vents = Ringz.ar(
        Dust.ar(0.02),
        LFNoise0.kr(0.02).exprange(30, 90),
        LFNoise0.kr(0.1).range(3, 10)
    ) * 0.3;

    subContent = LPF.ar(plates + pressure, 60);
    midContent = HPF.ar(magma + vents, 60);

    Out.ar(subOut, subContent * amp * breath);
    Out.ar(out, Pan2.ar(midContent, LFNoise1.kr(0.005).range(-0.3, 0.3)) * amp * breath);
}).add;

// Crystalline - the highs
SynthDef(\titans_crystal, { |out=0, amp=1, breathBus=0|
    var static, sparks, shimmer, ice, sig;
    var breath = In.kr(breathBus);

    static = HPF.ar(WhiteNoise.ar(0.1), 9000);
    static = static * LFNoise1.kr(0.08).range(0.2, 1);

    sparks = Mix.fill(10, {
        var trig = Dust.ar(LFNoise0.kr(0.2).range(2, 25));
        var freq = LFNoise0.kr(0.4).exprange(7000, 17000);
        Ringz.ar(trig, freq, 0.001) * 0.1;
    });
    sparks = Splay.ar(sparks, 0.7);

    shimmer = Mix.fill(6, { |i|
        var freq = 11000 + (i * 500) + LFNoise1.kr(0.15).range(-80, 80);
        SinOsc.ar(freq, 0, LFNoise1.kr(0.2).range(0, 0.02));
    });
    shimmer = Pan2.ar(shimmer, LFNoise1.kr(0.1).range(-0.4, 0.4));

    ice = SinOsc.ar(
        Demand.kr(Dust.kr(0.2), 0, Dseq([0,0,14500,0,0,16200,0,15000,0,0], inf)),
        0,
        Decay2.ar(Dust.ar(0.2), 0.001, 0.04) * 0.15
    );
    ice = Pan2.ar(ice, LFNoise0.kr(0.4).range(-1, 1));

    sig = HPF.ar(static + sparks + shimmer + ice, 5000);
    Out.ar(out, sig * amp * breath);
}).add;

// Granular - the chaos
SynthDef(\titans_grain, { |out=0, amp=1, breathBus=0|
    var grains, bursts, stutter, sig;
    var breath = In.kr(breathBus);

    grains = Mix.fill(15, {
        var rate = LFNoise0.kr(0.4).exprange(40, 400);
        var freq = LFNoise0.kr(0.8).exprange(150, 10000);
        Pan2.ar(
            Ringz.ar(Impulse.ar(rate), freq, 0.0004) * 0.04,
            LFNoise1.kr(1.5).range(-1, 1)
        );
    });

    bursts = Mix.fill(6, {
        var burstRate = LFNoise0.kr(0.25).exprange(80, 800);
        var burstAmp = LFNoise1.kr(0.4).range(0, 1).pow(4);
        var freq = LFNoise0.kr(1.5).exprange(300, 7000);
        Pan2.ar(
            Ringz.ar(Impulse.ar(burstRate) * burstAmp, freq, 0.0006) * 0.08,
            LFNoise0.kr(0.8).range(-1, 1)
        );
    });

    stutter = Mix.fill(4, {
        var baseRate = LFNoise0.kr(0.08).exprange(15, 60);
        var freq = LFNoise0.kr(0.4).exprange(400, 5000);
        Pan2.ar(
            SinOsc.ar(freq, 0, Decay.ar(Impulse.ar(baseRate * LFNoise0.kr(baseRate).range(1, 6)), 0.002) * 0.1),
            LFNoise1.kr(0.4).range(-1, 1)
        );
    });

    sig = HPF.ar(grains + bursts + stutter, 120);
    Out.ar(out, sig * amp * breath);
}).add;

// Glacial - the slow
SynthDef(\titans_glacial, { |out=0, subOut=0, amp=1, breathBus=0|
    var glacier, eons, breath_osc, shift;
    var subContent, midContent;
    var breath = In.kr(breathBus);

    glacier = Mix.fill(5, { |i|
        var freq = (28 + (i * 12)) * LFNoise1.kr(0.002).range(0.96, 1.04);
        SinOsc.ar(freq * [1, 1.003], 0, LFNoise1.kr(0.004).range(0.1, 0.35));
    });

    eons = LPF.ar(
        BrownNoise.ar(0.4),
        LFNoise1.kr(0.002).exprange(35, 300).lag(12)
    );

    breath_osc = SinOsc.ar(
        LFNoise1.kr(0.001).exprange(22, 55),
        0,
        SinOsc.kr(0.013).range(0, 0.4)
    );

    shift = Ringz.ar(
        Dust.ar(0.008),
        LFNoise0.kr(0.008).exprange(35, 180),
        LFNoise0.kr(0.04).range(6, 18)
    ) * 0.5;

    subContent = LPF.ar(glacier.sum + breath_osc, 60);
    midContent = HPF.ar(eons + shift, 60);

    Out.ar(subOut, subContent * amp * breath);
    Out.ar(out, Pan2.ar(midContent, LFNoise1.kr(0.008).range(-0.7, 0.7)) * amp * breath);
}).add;

// Donut - the extremes
SynthDef(\titans_donut, { |out=0, subOut=0, amp=1, breathBus=0|
    var abyss, pressure, low;
    var static, glass, ghost, high;
    var breath = In.kr(breathBus);

    abyss = Mix.fill(3, {
        var freq = LFNoise1.kr(0.006).exprange(10, 35);
        SinOsc.ar(freq, 0, LFNoise1.kr(0.015).range(0.15, 0.45));
    });
    pressure = LPF.ar(BrownNoise.ar(0.4), LFNoise1.kr(0.008).exprange(25, 70));
    low = LPF.ar(abyss + pressure, 60);

    static = HPF.ar(PinkNoise.ar(0.08), 11000);
    glass = Mix.fill(8, {
        var trig = Dust.ar(LFNoise0.kr(0.12).range(0.3, 6));
        var freq = LFNoise0.kr(0.25).exprange(10000, 17000);
        Ringz.ar(trig, freq, 0.002) * 0.06;
    });
    glass = Splay.ar(glass, 0.85);
    ghost = Mix.fill(4, { |i|
        var freq = 11000 + (i * 1800) + LFNoise1.kr(0.04).range(-150, 150);
        SinOsc.ar(freq, 0, LFNoise1.kr(0.08).range(0, 0.015));
    });
    ghost = Pan2.ar(ghost, LFNoise1.kr(0.06).range(-0.5, 0.5));
    high = HPF.ar(static + glass + ghost, 9000);

    Out.ar(subOut, low * amp * breath);
    Out.ar(out, high * SinOsc.kr(0.04, pi).range(0.4, 1) * amp * breath);
}).add;

// Mids - the life
SynthDef(\titans_mids, { |out=0, amp=1, breathBus=0|
    var creatures, drone, sig;
    var breath = In.kr(breathBus);

    creatures = Mix.fill(8, {
        var trig = Dust.ar(LFNoise0.kr(0.12).range(0.3, 6));
        var freq = LFNoise0.kr(0.2).exprange(200, 4000);
        var ring = LFNoise0.kr(0.3).range(0.02, 0.2);
        Pan2.ar(Ringz.ar(trig, freq, ring) * 0.25, LFNoise1.kr(0.15).range(-0.9, 0.9));
    });

    drone = Mix.fill(4, { |i|
        var freq = LFNoise1.kr(0.01).exprange(300, 1200) * (i + 1).sqrt;
        SinOsc.ar(freq * [1, 1.005], 0, LFNoise1.kr(0.02).range(0.02, 0.08));
    });
    drone = BPF.ar(drone + PinkNoise.ar(0.15), LFNoise1.kr(0.008).exprange(400, 2000), 0.3);

    sig = creatures + drone;
    Out.ar(out, sig * amp * breath);
}).add;

// Master - sub compression, reverb, limiting
SynthDef(\titans_master, { |out=0, in=0, subIn=0, reverbMix=0.5, reverbRoom=0.85|
    var main, sub, mix;

    main = In.ar(in, 2);
    sub = In.ar(subIn, 1);

    // Compress and mono the sub
    sub = Compander.ar(sub, sub, 0.3, 1, 0.4, 0.01, 0.3);
    sub = [sub, sub]; // mono center

    // Combine
    mix = sub + main;

    // Reverb on mids/highs only
    mix = LPF.ar(mix, 80) + FreeVerb2.ar(
        HPF.ar(mix[0], 80),
        HPF.ar(mix[1], 80),
        reverbMix,
        reverbRoom,
        0.25
    );

    // Saturation + limiting
    mix = (mix * 1.3).tanh * 0.75;
    mix = Limiter.ar(mix, 0.94);

    Out.ar(out, mix);
}).add;

"SynthDefs loaded.".postln;
)

// ==================== 3. BUSES & GROUPS ====================
(
// Buses
~breathBus = Bus.control(s, 1);
~mainBus = Bus.audio(s, 2);
~subBus = Bus.audio(s, 1);

// Groups (order matters for routing)
~srcGroup = Group.new;
~fxGroup = Group.after(~srcGroup);

"Buses and groups ready.".postln;
)

// ==================== 4. START SYNTHS ====================
(
// Master breath
~breath = Synth(\titans_breath, [
    \out, ~breathBus,
    \rate, 0.012,
    \min, 0.7,
    \max, 1
], ~srcGroup);

// Sources - add/remove these freely
~sub = Synth(\titans_sub, [
    \out, ~mainBus,
    \subOut, ~subBus,
    \amp, 1,
    \breathBus, ~breathBus
], ~srcGroup);

~crystal = Synth(\titans_crystal, [
    \out, ~mainBus,
    \amp, 0.9,
    \breathBus, ~breathBus
], ~srcGroup);

~grain = Synth(\titans_grain, [
    \out, ~mainBus,
    \amp, 0.7,
    \breathBus, ~breathBus
], ~srcGroup);

~glacial = Synth(\titans_glacial, [
    \out, ~mainBus,
    \subOut, ~subBus,
    \amp, 0.8,
    \breathBus, ~breathBus
], ~srcGroup);

~donut = Synth(\titans_donut, [
    \out, ~mainBus,
    \subOut, ~subBus,
    \amp, 1,
    \breathBus, ~breathBus
], ~srcGroup);

~mids = Synth(\titans_mids, [
    \out, ~mainBus,
    \amp, 0.8,
    \breathBus, ~breathBus
], ~srcGroup);

// Master processing
~master = Synth(\titans_master, [
    \out, 0,
    \in, ~mainBus,
    \subIn, ~subBus,
    \reverbMix, 0.5,
    \reverbRoom, 0.85
], ~fxGroup);

"All synths running.".postln;
)

// ==================== CONTROLS ====================
// Adjust levels live:
~sub.set(\amp, 1);
~crystal.set(\amp, 0.9);
~grain.set(\amp, 0.7);
~glacial.set(\amp, 0.8);
~donut.set(\amp, 1);
~mids.set(\amp, 0.8);

// Adjust master:
~master.set(\reverbMix, 0.5);
~master.set(\reverbRoom, 0.85);

// Adjust breath:
~breath.set(\rate, 0.012); // slower = longer cycles
~breath.set(\min, 0.7);
~breath.set(\max, 1);

// ==================== KILL INDIVIDUAL SYNTHS ====================
// ~sub.free;
// ~crystal.free;
// ~grain.free;
// ~glacial.free;
// ~donut.free;
// ~mids.free;

// ==================== RESTART A SYNTH ====================
// ~sub = Synth(\titans_sub, [\out, ~mainBus, \subOut, ~subBus, \amp, 1, \breathBus, ~breathBus], ~srcGroup);

// ==================== KILL EVERYTHING ====================
// ~srcGroup.free; ~fxGroup.free;

// ==================== FULL CLEANUP ====================
(
~breath.free; ~sub.free; ~crystal.free; ~grain.free;
~glacial.free; ~donut.free; ~mids.free; ~master.free;
~srcGroup.free; ~fxGroup.free;
~breathBus.free; ~mainBus.free; ~subBus.free;
"Cleaned up.".postln;
)
