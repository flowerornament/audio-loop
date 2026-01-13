// TITANS
// A journey through extremes
// Let it run. Walk away. Come back.

(
{
    var mix;
    var subterranean, crystalline, granular, glacial, donut;
    var subMix, crystalMix, grainMix, glacialMix, donutMix;
    var masterBreath, drift;

    // MASTER BREATH - everything pulses together, very slow
    masterBreath = SinOsc.kr(0.012).range(0.7, 1); // ~83 second cycle

    // DRIFT - controls which world we're in
    // Each fader moves independently at different rates
    subMix = LFNoise1.kr(0.008).range(0, 1).lag(15);      // ~2 min drift, 15s lag
    crystalMix = LFNoise1.kr(0.006).range(0, 1).lag(20);  // ~2.7 min drift
    grainMix = LFNoise1.kr(0.004).range(0, 1).lag(12);    // ~4 min drift
    glacialMix = LFNoise1.kr(0.003).range(0, 1).lag(25);  // ~5.5 min drift
    donutMix = LFNoise1.kr(0.005).range(0, 1).lag(18);    // ~3.3 min drift

    // ==================== SUBTERRANEAN ====================
    subterranean = {
        var plates, magma, pressure, vents;

        plates = Mix.fill(4, {
            var freq = LFNoise1.kr(0.01).exprange(8, 25);
            SinOsc.ar(freq, 0, LFNoise1.kr(0.02).range(0.15, 0.4));
        });

        magma = LPF.ar(BrownNoise.ar(0.5), LFNoise1.kr(0.008).exprange(20, 70));
        magma = Pan2.ar(magma, LFNoise1.kr(0.005).range(-0.3, 0.3));

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

        LPF.ar(plates + magma + pressure + vents, 100);
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

        HPF.ar(static + sparks + shimmer + ice, 5000);
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

        grains + bursts + stutter;
    }.value;

    // ==================== GLACIAL ====================
    glacial = {
        var glacier, eons, breath, shift;

        glacier = Mix.fill(5, { |i|
            var freq = (28 + (i * 12)) * LFNoise1.kr(0.002).range(0.96, 1.04);
            SinOsc.ar(freq * [1, 1.003], 0, LFNoise1.kr(0.004).range(0.1, 0.35));
        });

        eons = LPF.ar(
            BrownNoise.ar(0.4),
            LFNoise1.kr(0.002).exprange(35, 300).lag(12)
        );
        eons = Pan2.ar(eons, LFNoise1.kr(0.001).range(-0.4, 0.4));

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
        shift = Pan2.ar(shift, LFNoise1.kr(0.008).range(-0.7, 0.7));

        LPF.ar(glacier + eons + breath + shift, 400);
    }.value;

    // ==================== DONUT HOLE ====================
    donut = {
        var abyss, pressure, low;
        var static, glass, ghost, high;

        // Deep
        abyss = Mix.fill(3, {
            var freq = LFNoise1.kr(0.006).exprange(10, 35);
            SinOsc.ar(freq, 0, LFNoise1.kr(0.015).range(0.15, 0.45));
        });
        pressure = LPF.ar(BrownNoise.ar(0.4), LFNoise1.kr(0.008).exprange(25, 70));
        low = LPF.ar(abyss + pressure, 70);

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

        // Opposite breathing
        (low * SinOsc.kr(0.04).range(0.4, 1)) +
        (high * SinOsc.kr(0.04, pi).range(0.4, 1));
    }.value;

    // ==================== THE MIX ====================
    mix = (subterranean * subMix * 1.2) +
          (crystalline * crystalMix * 0.9) +
          (granular * grainMix * 0.7) +
          (glacial * glacialMix * 1.0) +
          (donut * donutMix * 1.1);

    // Apply master breath
    mix = mix * masterBreath;

    // Final processing - big space
    mix = FreeVerb2.ar(mix[0], mix[1],
        LFNoise1.kr(0.01).range(0.4, 0.8), // reverb mix drifts
        LFNoise1.kr(0.008).range(0.7, 0.99), // room size drifts
        0.2
    );

    // Gentle saturation before limiting
    mix = (mix * 1.5).tanh * 0.8;
    mix = Limiter.ar(mix, 0.94);
    mix;
}.play;
)
