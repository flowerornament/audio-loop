// TITANS v2
// Sub-bass managed properly

(
{
    var mix;
    var subterranean, crystalline, granular, glacial, donut;
    var subMix, crystalMix, grainMix, glacialMix, donutMix;
    var masterBreath, drift;

    // SUB MANAGEMENT
    var subBus, subMono, subFiltered;
    var subGate; // which world owns the sub right now

    // MID LAYER
    var midCreatures, midDrone, midMix, mids;

    // MASTER BREATH
    masterBreath = SinOsc.kr(0.012).range(0.7, 1);

    // DRIFT - controls which world we're in
    subMix = LFNoise1.kr(0.008).range(0, 1).lag(15);
    crystalMix = LFNoise1.kr(0.006).range(0, 1).lag(20);
    grainMix = LFNoise1.kr(0.004).range(0, 1).lag(12);
    glacialMix = LFNoise1.kr(0.003).range(0, 1).lag(25);
    donutMix = LFNoise1.kr(0.005).range(0, 1).lag(18);

    // MID MIX - always somewhat present
    midMix = LFNoise1.kr(0.007).range(0.3, 1).lag(10);

    // SUB OWNERSHIP - only the loudest world gets the sub
    // This is the creative solution: they take turns
    subGate = [subMix, glacialMix, donutMix];
    subGate = subGate / (subGate.sum.max(0.001)); // normalize to 1

    // ==================== SUBTERRANEAN ====================
    subterranean = {
        var plates, magma, pressure, vents;
        var subContent, midContent;

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

        // Split: sub goes to sub bus, rest stays
        subContent = LPF.ar(plates + pressure, 60);
        midContent = HPF.ar(magma + vents, 60);

        [subContent, Pan2.ar(midContent, LFNoise1.kr(0.005).range(-0.3, 0.3))];
    }.value;

    // ==================== CRYSTALLINE ====================
    crystalline = {
        var static, sparks, shimmer, ice;

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

        // No sub content - all highs
        [Silent.ar, HPF.ar(static + sparks + shimmer + ice, 5000)];
    }.value;

    // ==================== GRANULAR ====================
    granular = {
        var grains, bursts, stutter;

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

        // HPF the grains - no sub mud
        [Silent.ar, HPF.ar(grains + bursts + stutter, 120)];
    }.value;

    // ==================== GLACIAL ====================
    glacial = {
        var glacier, eons, breath, shift;
        var subContent, midContent;

        glacier = Mix.fill(5, { |i|
            var freq = (28 + (i * 12)) * LFNoise1.kr(0.002).range(0.96, 1.04);
            SinOsc.ar(freq * [1, 1.003], 0, LFNoise1.kr(0.004).range(0.1, 0.35));
        });

        eons = LPF.ar(
            BrownNoise.ar(0.4),
            LFNoise1.kr(0.002).exprange(35, 300).lag(12)
        );

        breath = SinOsc.ar(
            LFNoise1.kr(0.001).exprange(22, 55),
            0,
            SinOsc.kr(0.013).range(0, 0.4)
        );

        shift = Ringz.ar(
            Dust.ar(0.008),
            LFNoise0.kr(0.008).exprange(35, 180),
            LFNoise0.kr(0.04).range(6, 18)
        ) * 0.5;

        // Split sub and mid
        subContent = LPF.ar(glacier.sum + breath, 60);
        midContent = HPF.ar(eons + shift, 60);
        midContent = Pan2.ar(midContent, LFNoise1.kr(0.008).range(-0.7, 0.7));

        [subContent, midContent];
    }.value;

    // ==================== DONUT HOLE ====================
    donut = {
        var abyss, pressure, low;
        var static, glass, ghost, high;

        // Deep - this is the sub
        abyss = Mix.fill(3, {
            var freq = LFNoise1.kr(0.006).exprange(10, 35);
            SinOsc.ar(freq, 0, LFNoise1.kr(0.015).range(0.15, 0.45));
        });
        pressure = LPF.ar(BrownNoise.ar(0.4), LFNoise1.kr(0.008).exprange(25, 70));
        low = LPF.ar(abyss + pressure, 60); // sub only

        // High
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

        // Opposite breathing on high only - sub stays steady
        [low, high * SinOsc.kr(0.04, pi).range(0.4, 1)];
    }.value;

    // ==================== SUB BUS - THE KEY ====================
    // Collect all sub content, apply ownership gate, sum to MONO
    subBus = (subterranean[0] * subMix * subGate[0]) +
             (glacial[0] * glacialMix * subGate[1]) +
             (donut[0] * donutMix * subGate[2]);

    // MONO SUM the sub - no phase issues
    subMono = Mix.ar(subBus) * 0.7;

    // Gentle compression on sub to glue it
    subMono = Compander.ar(subMono, subMono,
        thresh: 0.3,
        slopeBelow: 1,
        slopeAbove: 0.4,
        clampTime: 0.01,
        relaxTime: 0.3
    );

    // Sub as mono center
    subFiltered = [subMono, subMono];

    // ==================== THE MIDS - LIFE ====================
    // Creatures that live between the extremes
    midCreatures = Mix.fill(8, {
        var trig, freq, pan, ring;
        trig = Dust.ar(LFNoise0.kr(0.12).range(0.3, 6) * masterBreath);
        freq = LFNoise0.kr(0.2).exprange(200, 4000);
        pan = LFNoise1.kr(0.15).range(-0.9, 0.9);
        ring = LFNoise0.kr(0.3).range(0.02, 0.2);
        Pan2.ar(Ringz.ar(trig, freq, ring) * 0.25, pan);
    });

    // Mid drone - slowly shifting resonance
    midDrone = Mix.fill(4, { |i|
        var freq = LFNoise1.kr(0.01).exprange(300, 1200) * (i + 1).sqrt;
        var amp = LFNoise1.kr(0.02).range(0.02, 0.08);
        SinOsc.ar(freq * [1, 1.005], 0, amp);
    });
    midDrone = BPF.ar(midDrone + (PinkNoise.ar(0.15)), LFNoise1.kr(0.008).exprange(400, 2000), 0.3);

    // Combine mids
    mids = midCreatures + midDrone;
    mids = mids * midMix;

    // ==================== MID/HIGH BUS ====================
    // Everything else keeps its stereo
    mix = (subterranean[1] * subMix * 1.0) +
          (crystalline[1] * crystalMix * 0.9) +
          (granular[1] * grainMix * 0.7) +
          (glacial[1] * glacialMix * 0.8) +
          (donut[1] * donutMix * 1.0) +
          (mids * 0.8);

    // ==================== FINAL MIX ====================
    // Combine mono sub + stereo mid/high
    mix = subFiltered + mix;

    // Apply master breath
    mix = mix * masterBreath;

    // Final reverb - but NOT on sub
    mix = (LPF.ar(mix, 80)) + // dry sub
          FreeVerb2.ar(
              HPF.ar(mix[0], 80),
              HPF.ar(mix[1], 80),
              LFNoise1.kr(0.01).range(0.4, 0.75),
              LFNoise1.kr(0.008).range(0.7, 0.95),
              0.25
          );

    // Saturation + limiting
    mix = (mix * 1.3).tanh * 0.75;
    mix = Limiter.ar(mix, 0.94);
    mix;
}.play;
)
