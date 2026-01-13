{
    var airplane, enya, baby, phoneSpeaker, mix;
    var enyaPad, enyaMelody, enyaVerb;
    var babyForm, babyCry, babyRhythm, emBPM;
    var engineRumble, cabinAir, seatRattle;

    // === AIRPLANE AMBIENCE ===
    // Low engine rumble
    engineRumble = LPF.ar(BrownNoise.ar(0.4), 150) +
                   SinOsc.ar([58, 62], 0, 0.15) +  // engine harmonics
                   LPF.ar(PinkNoise.ar(0.1), 200);

    // Cabin air hiss
    cabinAir = HPF.ar(PinkNoise.ar(0.08), 2000);
    cabinAir = cabinAir + BPF.ar(WhiteNoise.ar(0.03), 4000, 0.5);

    // Occasional seat rattle
    seatRattle = Dust.ar(0.5) * BPF.ar(PinkNoise.ar(1), 800, 0.3) *
                 EnvGen.ar(Env.perc(0.01, 0.1), Dust.ar(0.5)) * 0.1;

    airplane = (engineRumble + cabinAir + seatRattle) * 0.5;

    // === ENYA FROM PHONE SPEAKER ===
    // Ethereal pad - slow, reverby, new age
    enyaPad = Mix.fill(4, { |i|
        var freq = [196, 293.66, 392, 493.88][i]; // G major add9
        var vib = SinOsc.kr(LFNoise1.kr(0.1).range(4, 6), i, 0.01, 1);
        SinOsc.ar(freq * vib, 0, 0.1) *
        EnvGen.kr(Env.sine(LFNoise1.kr(0.05).range(4, 8)), Dust.kr(0.15))
    });

    // Simple "Orinoco Flow" style melody - pentatonic, slow
    enyaMelody = SinOsc.ar(
        Demand.kr(Impulse.kr(0.5), 0,
            Dseq([392, 440, 523.25, 587.33, 659.25, 587.33, 523.25, 440], inf)
        ).lag(0.3),
        0, 0.08
    );

    enya = enyaPad + enyaMelody;
    enya = FreeVerb.ar(enya, 0.8, 0.9, 0.5); // Lots of reverb

    // Phone speaker effect - tinny, no bass, resonant mids
    phoneSpeaker = HPF.ar(enya, 400);
    phoneSpeaker = BPF.ar(phoneSpeaker, 2000, 0.8) * 2;
    phoneSpeaker = (phoneSpeaker * 3).tanh * 0.3; // Phone distortion
    phoneSpeaker = Pan2.ar(phoneSpeaker, 0.6); // Off to one side

    // === BABY CRYING TO EMINEM BEAT ===
    emBPM = 95; // Classic Eminem tempo
    babyRhythm = Impulse.kr(emBPM / 60); // Quarter notes

    // Baby formants - crying "waaah"
    babyForm = Formant.ar(
        fundfreq: LFNoise2.kr(3).range(400, 600), // Pitch wobble
        formfreq: LFNoise1.kr(5).range(1200, 2500), // Formant shift (mouth opening)
        bwfreq: LFNoise1.kr(2).range(200, 600)
    );

    // Shape into rhythmic bursts synced to beat
    babyCry = babyForm * EnvGen.ar(
        Env.perc(0.05, 0.3),
        Impulse.ar(emBPM / 60 * TIRand.kr(1, 2, babyRhythm)) // On-beat, sometimes double-time
    );

    // Add breath intake between cries
    babyCry = babyCry + (HPF.ar(PinkNoise.ar(0.1), 3000) *
        EnvGen.ar(Env.perc(0.1, 0.15), Impulse.ar(emBPM / 60)) *
        TRand.kr(0, 0.3, babyRhythm));

    babyCry = babyCry * 0.25;
    babyCry = Pan2.ar(babyCry, -0.5); // Other side of plane

    // === MIX ===
    mix = (airplane ! 2) + phoneSpeaker + babyCry;

    mix * 0.7
}
