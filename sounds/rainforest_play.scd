// RAINFOREST - for SuperCollider IDE
// Boot server first (Cmd+B), then run this block (Cmd+Enter)
// Stop with Cmd+.

(
{
    var floor, insects, frogs, birds, water, mix;
    var breath, density;

    // Global modulators - the forest breathes
    breath = SinOsc.kr(0.08).range(0.6, 1);
    density = LFNoise1.kr(0.05).range(0.7, 1.3);

    // FLOOR - deep earth
    floor = LPF.ar(BrownNoise.ar(0.25), 80) +
            LPF.ar(PinkNoise.ar(0.1), 180) +
            SinOsc.ar(LFNoise1.kr(0.04).exprange(22, 38), 0, 0.08 * breath);
    floor = Pan2.ar(floor, LFNoise1.kr(0.01).range(-0.08, 0.08)) * 0.5;

    // INSECTS - cicadas + crickets
    insects = Mix.fill(6, { |i|
        var freq, pan, amp;
        freq = (2200 + (i * 350)) * LFNoise1.kr(0.1).range(0.95, 1.05);
        pan = (i / 2.5) - 1.2;
        amp = LFNoise1.kr(0.15).range(0.015, 0.045) * breath;
        Pan2.ar(
            SinOsc.ar(freq, 0, amp) * SinOsc.ar(LFNoise0.kr(0.3).range(5, 18), 0, 0.5, 0.5),
            pan.clip(-1, 1)
        );
    });
    insects = insects + Mix.fill(4, { |i|
        var rate, freq, pan;
        rate = LFNoise0.kr(0.15).range(1.5, 12) * density;
        freq = LFNoise1.kr(0.05).exprange(2800, 7000);
        pan = [-0.8, 0.9, -0.5, 0.6][i];
        Pan2.ar(
            Ringz.ar(Impulse.ar(rate) * LFNoise1.kr(1).range(0.15, 1), freq, 0.012) * 0.04,
            pan
        );
    });
    insects = insects * breath;

    // FROGS - tree frogs + bullfrogs
    frogs = Mix.fill(5, { |i|
        var trig, freq, pan;
        trig = Dust.ar(LFNoise0.kr(0.1).range(0.8, 5) * density);
        freq = LFNoise0.kr(0.25).exprange(450, 9600);
        pan = [-0.7, 0.5, -0.3, 0.8, 0][i];
        Pan2.ar(
            Ringz.ar(trig, freq, LFNoise0.kr(0.5).range(0.06, 0.18)) * 0.92,
            pan
        );
    });
    frogs = frogs + Mix.fill(2, { |i|
        var trig, freq;
        trig = Dust.ar(LFNoise0.kr(0.05).range(0.2, 1.0) * density);
        freq = LFNoise0.kr(0.12).exprange(150, 4000);
        Pan2.ar(
            BPF.ar(PinkNoise.ar(1.5), freq, 0.3) * Decay2.ar(trig, 0.01, 0.35) * 4.45,
            [-0.6, 0.6][i]
        );
    });
    frogs = frogs * breath;

    // BIRDS
    birds = Mix.fill(4, { |i|
        var trig, freq, pan;
        trig = Dust.ar(LFNoise0.kr(0.08).range(0.08, 0.7) * density);
        freq = LFNoise0.kr(0.2).exprange(600, 2800);
        pan = [-0.75, 0.6, -0.4, 0.85][i];
        Pan2.ar(
            SinOsc.ar(freq * LFNoise1.kr(10).range(3.96, 6.04), 0, 0.14) *
            Decay2.ar(trig, 0.015, LFNoise0.kr(0.5).range(0.2, 0.5)),
            pan
        );
    });
    birds = FreeVerb.ar(birds, 0.55, 0.75, 0.35) * breath;

    // WATER - drips
    water = Mix.fill(5, { |i|
        var trig, freq, pan;
        trig = Dust.ar(LFNoise0.kr(0.12).range(0.2, 2.5));
        freq = LFNoise0.kr(0.3).exprange(1200, 8000);
        pan = [-0.9, 0.7, -0.5, 0.3, 0.9][i];
        Pan2.ar(Ringz.ar(trig, freq, 0.015) * 4.96, pan);
    });

    // MIX
    mix = floor + insects + frogs + birds + water;
    mix = FreeVerb2.ar(mix[0], mix[1], 0.45, 0.88, 0.35);
    mix = Limiter.ar(mix * 1.1, 0.92);
    mix;
}.play;
)
