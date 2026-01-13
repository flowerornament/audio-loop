// THE FOREST IS AWARE
// Something lives underneath. The creatures know.

(
{
    var floor, insects, frogs, birds, water, mix;
    var breath, density;
    var entity, entityPresence, fear;
    var pulse, heartbeat;

    // THE ENTITY - something massive, subsonic, slowly waking
    entityPresence = LFNoise1.kr(0.02).range(0, 1).lag(8); // very slow, smoothed
    entity = SinOsc.ar(
        LFNoise1.kr(0.01).exprange(14, 19), // below hearing, felt not heard
        0,
        entityPresence * 0.4
    );
    entity = entity + SinOsc.ar(
        LFNoise1.kr(0.008).exprange(28, 38) * [1, 1.01], // beating frequencies
        0,
        entityPresence * 0.25
    );
    // when it stirs, harmonics appear
    entity = entity + (
        Blip.ar(LFNoise1.kr(0.01).exprange(55, 65), LFNoise1.kr(0.1).range(2, 12)) *
        entityPresence.pow(3) * 0.15 // only audible when presence is strong
    );

    // FEAR - creatures respond to the entity
    fear = 1 - (entityPresence * 0.85); // when entity is present, fear dampens activity

    // HEARTBEAT - the forest has a pulse (not quite 4/4, unsettling)
    pulse = Impulse.kr(0.7); // ~42 BPM, slow dread
    heartbeat = SinOsc.ar(38, 0, Decay2.ar(Impulse.ar(0.7), 0.01, 0.4) * 0.3);
    heartbeat = heartbeat + SinOsc.ar(19, 0, Decay2.ar(Impulse.ar(0.35), 0.05, 0.8) * 0.2);

    // Global modulators
    breath = SinOsc.kr(0.08).range(0.6, 1) * fear;
    density = LFNoise1.kr(0.05).range(0.7, 1.3) * fear;

    // FLOOR - deeper, more ominous
    floor = LPF.ar(BrownNoise.ar(0.25), 60) +
            LPF.ar(PinkNoise.ar(0.1), 120);
    floor = Pan2.ar(floor, LFNoise1.kr(0.01).range(-0.1, 0.1)) * 0.4;

    // INSECTS - they go quiet when IT stirs
    insects = Mix.fill(8, { |i|
        var freq, pan, amp, trem;
        freq = (1800 + (i * 450)) * LFNoise1.kr(0.15).range(0.93, 1.07);
        pan = (i / 3.5) - 1.1;
        trem = LFPulse.kr(LFNoise0.kr(0.2).range(8, 25), 0, 0.5);
        amp = LFNoise1.kr(0.2).range(0.02, 0.07) * breath * trem;
        Pan2.ar(SinOsc.ar(freq, 0, amp), pan.clip(-1, 1));
    });
    insects = insects + Mix.fill(5, { |i|
        var rate, freq, pan;
        rate = LFNoise0.kr(0.2).range(3, 18) * density;
        freq = LFNoise1.kr(0.08).exprange(3500, 11000);
        pan = LFNoise1.kr(0.1).range(-1, 1);
        Pan2.ar(
            Ringz.ar(Impulse.ar(rate) * LFNoise1.kr(2).range(0.1, 1), freq, 0.008) * 0.05,
            pan
        );
    });

    // FROGS - calling into the void, wider range, wilder
    frogs = Mix.fill(7, { |i|
        var trig, freq, pan, ring;
        trig = Dust.ar(LFNoise0.kr(0.15).range(0.5, 6) * density);
        freq = LFNoise0.kr(0.3).exprange(200, 8000);
        pan = LFNoise1.kr(0.08).range(-1, 1);
        ring = LFNoise0.kr(0.4).range(0.03, 0.25);
        Pan2.ar(Ringz.ar(trig, freq, ring) * 0.6, pan);
    });
    // the deep ones - they call to the entity
    frogs = frogs + Mix.fill(3, { |i|
        var trig, freq;
        trig = Dust.ar(LFNoise0.kr(0.03).range(0.05, 0.4) * (1 + entityPresence)); // MORE active when entity stirs
        freq = LFNoise0.kr(0.08).exprange(60, 250);
        Pan2.ar(
            BPF.ar(PinkNoise.ar(2), freq, 0.2) * Decay2.ar(trig, 0.02, 0.5) * 2.5,
            LFNoise1.kr(0.03).range(-0.4, 0.4)
        );
    });
    frogs = frogs * breath;

    // BIRDS - nervous, scattered, sometimes frozen
    birds = Mix.fill(5, { |i|
        var trig, freq, pan, frozen;
        frozen = LFNoise0.kr(0.1).range(0, 1) > (0.3 + (entityPresence * 0.5)); // more likely to freeze when entity present
        trig = Dust.ar(LFNoise0.kr(0.1).range(0.1, 1.2) * density * frozen);
        freq = LFNoise0.kr(0.3).exprange(400, 4500);
        pan = LFNoise1.kr(0.2).range(-0.9, 0.9);
        Pan2.ar(
            SinOsc.ar(freq * LFNoise1.kr(15).range(0.92, 1.08), 0, 0.18) *
            Decay2.ar(trig, 0.01, LFNoise0.kr(0.3).range(0.1, 0.6)),
            pan
        );
    });
    birds = FreeVerb.ar(birds, 0.7, 0.85, 0.3) * breath;

    // WATER - drips echo in the darkness
    water = Mix.fill(6, { |i|
        var trig, freq, pan, verb;
        trig = Dust.ar(LFNoise0.kr(0.15).range(0.1, 3));
        freq = LFNoise0.kr(0.4).exprange(800, 9000);
        pan = LFNoise1.kr(0.3).range(-1, 1);
        Pan2.ar(
            Ringz.ar(trig, freq, 0.02) * 0.4,
            pan
        );
    });
    water = FreeVerb.ar(water, 0.8, 0.95, 0.2); // very wet, cavernous

    // SOMETHING ELSE - brief glimpses, wrong sounds
    // occasionally a tone that shouldn't be there
    water = water + Pan2.ar(
        SinOsc.ar(
            Demand.kr(Dust.kr(0.08), 0, Dseq([0, 0, 0, 523.25, 0, 0, 659.25, 0], inf)),
            0,
            Decay2.ar(Dust.ar(0.08), 0.1, 2) * 0.06
        ) * entityPresence.pow(2),
        LFNoise1.kr(0.5).range(-1, 1)
    );

    // MIX
    mix = floor + entity + heartbeat + insects + frogs + birds + water;

    // the entity creates pressure - gentle compression when it swells
    mix = mix * (1 - (entityPresence * 0.3));
    mix = FreeVerb2.ar(mix[0], mix[1], 0.5, 0.92, 0.25);
    mix = Limiter.ar(mix * 1.2, 0.94);
    mix;
}.play;
)
