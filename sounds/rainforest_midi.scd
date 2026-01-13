// RAINFOREST - MIDI CONTROLLABLE
// 1. Boot server (Cmd+B)
// 2. Run the setup block first
// 3. Then run the synth block
// 4. Twist knobs

// ========== SETUP (run this first) ==========
(
MIDIClient.init;
MIDIIn.connectAll;

// Control buses
~entityLevel = Bus.control(s, 1).set(0.3);
~fear = Bus.control(s, 1).set(0.5);
~density = Bus.control(s, 1).set(1);
~frogAmp = Bus.control(s, 1).set(0.6);
~birdAmp = Bus.control(s, 1).set(0.5);
~insectAmp = Bus.control(s, 1).set(0.5);
~waterAmp = Bus.control(s, 1).set(0.4);
~reverbMix = Bus.control(s, 1).set(0.5);
~weirdness = Bus.control(s, 1).set(0.2);
~heartbeatAmp = Bus.control(s, 1).set(0.3);

// MIDI CC mappings - adjust these to your controller
// Using standard CC numbers, change as needed
MIDIdef.cc(\entity, { |val| ~entityLevel.set(val/127); }, 1);      // CC1 (mod wheel)
MIDIdef.cc(\fear, { |val| ~fear.set(val/127); }, 2);               // CC2
MIDIdef.cc(\density, { |val| ~density.set(val/127 * 2); }, 3);     // CC3 (0-2 range)
MIDIdef.cc(\frogs, { |val| ~frogAmp.set(val/127 * 1.5); }, 4);     // CC4
MIDIdef.cc(\birds, { |val| ~birdAmp.set(val/127); }, 5);           // CC5
MIDIdef.cc(\insects, { |val| ~insectAmp.set(val/127); }, 6);       // CC6
MIDIdef.cc(\water, { |val| ~waterAmp.set(val/127); }, 7);          // CC7 (volume)
MIDIdef.cc(\reverb, { |val| ~reverbMix.set(val/127); }, 8);        // CC8
MIDIdef.cc(\weird, { |val| ~weirdness.set(val/127); }, 9);         // CC9
MIDIdef.cc(\heartbeat, { |val| ~heartbeatAmp.set(val/127); }, 10); // CC10 (pan, repurposed)

"MIDI Setup Complete.
CC1: Entity presence
CC2: Fear (dampens creatures)
CC3: Density (activity level)
CC4: Frogs
CC5: Birds
CC6: Insects
CC7: Water
CC8: Reverb
CC9: Weirdness
CC10: Heartbeat".postln;
)

// ========== SYNTH (run this second) ==========
(
{
    var floor, insects, frogs, birds, water, mix;
    var entity, heartbeat;
    var entityLevel, fear, density, frogAmp, birdAmp, insectAmp, waterAmp, reverbMix, weirdness, heartbeatAmp;

    // Read from control buses
    entityLevel = In.kr(~entityLevel);
    fear = In.kr(~fear);
    density = In.kr(~density);
    frogAmp = In.kr(~frogAmp);
    birdAmp = In.kr(~birdAmp);
    insectAmp = In.kr(~insectAmp);
    waterAmp = In.kr(~waterAmp);
    reverbMix = In.kr(~reverbMix);
    weirdness = In.kr(~weirdness);
    heartbeatAmp = In.kr(~heartbeatAmp);

    // Smooth the controls to avoid clicks
    entityLevel = entityLevel.lag(0.3);
    fear = fear.lag(0.2);
    density = density.lag(0.1);

    // THE ENTITY
    entity = SinOsc.ar(LFNoise1.kr(0.01).exprange(14, 22), 0, entityLevel * 0.5);
    entity = entity + SinOsc.ar(
        LFNoise1.kr(0.008).exprange(28, 42) * [1, 1.01],
        0,
        entityLevel * 0.3
    );
    entity = entity + (
        Blip.ar(LFNoise1.kr(0.01).exprange(50, 70), LFNoise1.kr(0.1).range(2, 15)) *
        entityLevel.pow(2) * 0.2
    );

    // HEARTBEAT
    heartbeat = SinOsc.ar(38, 0, Decay2.ar(Impulse.ar(0.7), 0.01, 0.4) * heartbeatAmp);
    heartbeat = heartbeat + SinOsc.ar(19, 0, Decay2.ar(Impulse.ar(0.35), 0.05, 0.8) * heartbeatAmp * 0.7);

    // FLOOR
    floor = LPF.ar(BrownNoise.ar(0.25), 70 + (weirdness * 100)) +
            LPF.ar(PinkNoise.ar(0.1), 150);
    floor = Pan2.ar(floor, LFNoise1.kr(0.01).range(-0.1, 0.1)) * 0.4 * fear;

    // INSECTS
    insects = Mix.fill(8, { |i|
        var freq, pan, amp;
        freq = (1800 + (i * 400 * (1 + weirdness))) * LFNoise1.kr(0.12).range(0.94, 1.06);
        pan = (i / 3.5) - 1.1;
        amp = LFNoise1.kr(0.2).range(0.02, 0.08) * fear * insectAmp;
        Pan2.ar(
            SinOsc.ar(freq, 0, amp) * LFPulse.kr(LFNoise0.kr(0.3).range(6, 20), 0, 0.5),
            pan.clip(-1, 1)
        );
    });
    insects = insects + Mix.fill(5, { |i|
        var rate, freq;
        rate = LFNoise0.kr(0.2).range(2, 15) * density;
        freq = LFNoise1.kr(0.06).exprange(3000, 10000 + (weirdness * 5000));
        Pan2.ar(
            Ringz.ar(Impulse.ar(rate) * LFNoise1.kr(1.5).range(0.1, 1), freq, 0.01) * 0.05 * insectAmp,
            LFNoise1.kr(0.1).range(-1, 1)
        );
    });

    // FROGS
    frogs = Mix.fill(7, { |i|
        var trig, freq, ring;
        trig = Dust.ar(LFNoise0.kr(0.12).range(0.4, 5) * density);
        freq = LFNoise0.kr(0.25).exprange(180, 6000 + (weirdness * 6000));
        ring = LFNoise0.kr(0.3).range(0.03, 0.2 + (weirdness * 0.3));
        Pan2.ar(
            Ringz.ar(trig, freq, ring) * frogAmp,
            LFNoise1.kr(0.1).range(-1, 1)
        );
    });
    // deep ones - respond to entity
    frogs = frogs + Mix.fill(3, { |i|
        var trig, freq;
        trig = Dust.ar(LFNoise0.kr(0.04).range(0.05, 0.5) * (1 + entityLevel));
        freq = LFNoise0.kr(0.1).exprange(50, 300);
        Pan2.ar(
            BPF.ar(PinkNoise.ar(2.5), freq, 0.25) * Decay2.ar(trig, 0.02, 0.6) * frogAmp * 1.5,
            LFNoise1.kr(0.04).range(-0.5, 0.5)
        );
    });
    frogs = frogs * fear;

    // BIRDS
    birds = Mix.fill(5, { |i|
        var trig, freq;
        trig = Dust.ar(LFNoise0.kr(0.08).range(0.08, 1) * density * fear);
        freq = LFNoise0.kr(0.25).exprange(350, 4000);
        Pan2.ar(
            SinOsc.ar(freq * LFNoise1.kr(12).range(0.9 - (weirdness * 0.5), 1.1 + (weirdness * 0.5)), 0, 0.2) *
            Decay2.ar(trig, 0.015, LFNoise0.kr(0.4).range(0.15, 0.5)),
            LFNoise1.kr(0.15).range(-0.9, 0.9)
        );
    });
    birds = FreeVerb.ar(birds, 0.6, 0.8, 0.3) * birdAmp;

    // WATER
    water = Mix.fill(6, { |i|
        var trig, freq;
        trig = Dust.ar(LFNoise0.kr(0.12).range(0.1, 2.5));
        freq = LFNoise0.kr(0.35).exprange(600, 8000);
        Pan2.ar(
            Ringz.ar(trig, freq, 0.015 + (weirdness * 0.05)) * waterAmp,
            LFNoise1.kr(0.25).range(-1, 1)
        );
    });

    // WRONG TONES (weirdness control)
    water = water + Pan2.ar(
        SinOsc.ar(
            Demand.kr(Dust.kr(0.05 + (weirdness * 0.2)), 0,
                Dseq([0, 523.25, 0, 0, 659.25, 0, 784, 0], inf)
            ),
            0,
            Decay2.ar(Dust.ar(0.05 + (weirdness * 0.2)), 0.1, 1.5) * weirdness * 0.15
        ),
        LFNoise1.kr(0.3).range(-1, 1)
    );

    // MIX
    mix = floor + entity + heartbeat + insects + frogs + birds + water;
    mix = mix * (1 - (entityLevel * 0.25));
    mix = FreeVerb2.ar(mix[0], mix[1], reverbMix, 0.9, 0.3);
    mix = Limiter.ar(mix * 1.1, 0.94);
    mix;
}.play;
)

// ========== CLEANUP (when done) ==========
// Cmd+. to stop sound
// Then run this to free buses:
(
~entityLevel.free;
~fear.free;
~density.free;
~frogAmp.free;
~birdAmp.free;
~insectAmp.free;
~waterAmp.free;
~reverbMix.free;
~weirdness.free;
~heartbeatAmp.free;
MIDIdef.freeAll;
"Cleaned up.".postln;
)
