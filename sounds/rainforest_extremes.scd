// EXTREMES - no middle ground
// Choose your violence: run ONE of these blocks

// ============ SUBTERRANEAN SMEAR ============
// Everything below 100Hz, decays measured in seconds
// The forest as tectonic event
(
{
    var mix;
    var plates, magma, pressure, vents;

    // Tectonic plates shifting
    plates = Mix.fill(4, {
        var freq = LFNoise1.kr(0.01).exprange(8, 25);
        var amp = LFNoise1.kr(0.02).range(0.2, 0.5);
        SinOsc.ar(freq, 0, amp);
    });
    plates = LPF.ar(plates, 40);

    // Magma - filtered noise, very slow movement
    magma = LPF.ar(BrownNoise.ar(0.6), LFNoise1.kr(0.008).exprange(20, 80));
    magma = magma + LPF.ar(PinkNoise.ar(0.3), 50);
    magma = Pan2.ar(magma, LFNoise1.kr(0.005).range(-0.3, 0.3));

    // Pressure building and releasing
    pressure = SinOsc.ar(
        LFNoise1.kr(0.003).exprange(12, 35),
        0,
        LFNoise1.kr(0.01).range(0, 1).lag(4) // 4 second lag = massive smear
    ) * 0.7;

    // Rare vents - when pressure releases
    vents = Ringz.ar(
        Dust.ar(0.03), // very rare
        LFNoise0.kr(0.02).exprange(30, 90),
        LFNoise0.kr(0.1).range(2, 8) // 2-8 second decay!
    ) * 0.4;

    mix = plates + magma + pressure + vents;
    mix = LPF.ar(mix, 100); // NOTHING above 100Hz
    mix = FreeVerb2.ar(mix[0], mix[1], 0.7, 0.99, 0.1);
    mix = Limiter.ar(mix * 1.5, 0.95);
    mix;
}.play;
)

// ============ CRYSTALLINE DUST ============
// Everything above 4kHz, decays measured in milliseconds
// The forest as static electricity
(
{
    var mix;
    var static, sparks, crackle, shimmer, ice;

    // Static field - high filtered noise
    static = HPF.ar(WhiteNoise.ar(0.15), 8000);
    static = static * LFNoise1.kr(0.1).range(0.3, 1);

    // Sparks - ultra short, ultra high
    sparks = Mix.fill(12, {
        var trig = Dust.ar(LFNoise0.kr(0.2).range(1, 30));
        var freq = LFNoise0.kr(0.5).exprange(6000, 18000);
        Ringz.ar(trig, freq, 0.001) * 0.15; // 1ms decay
    });
    sparks = Splay.ar(sparks, 0.8);

    // Crackle - impulse trains
    crackle = Mix.fill(6, {
        var rate = LFNoise0.kr(0.15).exprange(20, 200);
        var freq = LFNoise1.kr(0.1).exprange(8000, 16000);
        Ringz.ar(Impulse.ar(rate) * LFNoise1.kr(5).range(0, 1), freq, 0.0005) * 0.1;
    });
    crackle = Pan2.ar(crackle, LFNoise1.kr(0.3).range(-1, 1));

    // Shimmer - sine clusters way up high
    shimmer = Mix.fill(8, { |i|
        var freq = 12000 + (i * 400) + LFNoise1.kr(0.2).range(-100, 100);
        SinOsc.ar(freq, 0, LFNoise1.kr(0.3).range(0, 0.03));
    });
    shimmer = Pan2.ar(shimmer, LFNoise1.kr(0.1).range(-0.5, 0.5));

    // Ice - rare piercing tones
    ice = SinOsc.ar(
        Demand.kr(Dust.kr(0.3), 0, Dseq([0,0,0,14000,0,15500,0,0,16800,0], inf)),
        0,
        Decay2.ar(Dust.ar(0.3), 0.001, 0.05) * 0.2
    );
    ice = Pan2.ar(ice, LFNoise0.kr(0.5).range(-1, 1));

    mix = static + sparks + crackle + shimmer + ice;
    mix = HPF.ar(mix, 4000); // NOTHING below 4kHz
    mix = FreeVerb2.ar(mix[0], mix[1], 0.4, 0.7, 0.5);
    mix = Limiter.ar(mix * 2, 0.9);
    mix;
}.play;
)

// ============ GRANULAR VIOLENCE ============
// Everything as fast as possible, sub-millisecond
// The forest having a seizure
(
{
    var mix;
    var grains, bursts, stutter, chaos;

    // Grain cloud - hundreds of micro-events
    grains = Mix.fill(20, {
        var rate = LFNoise0.kr(0.5).exprange(50, 500); // 50-500 grains/sec
        var freq = LFNoise0.kr(1).exprange(100, 12000);
        var pan = LFNoise1.kr(2).range(-1, 1);
        Pan2.ar(
            Ringz.ar(Impulse.ar(rate), freq, 0.0003) * 0.05, // 0.3ms
            pan
        );
    });

    // Bursts - clusters of density
    bursts = Mix.fill(8, {
        var burstRate = LFNoise0.kr(0.3).exprange(100, 1000);
        var burstAmp = LFNoise1.kr(0.5).range(0, 1).pow(3); // mostly quiet, sometimes loud
        var freq = LFNoise0.kr(2).exprange(200, 8000);
        Pan2.ar(
            Ringz.ar(Impulse.ar(burstRate) * burstAmp, freq, 0.0005) * 0.1,
            LFNoise0.kr(1).range(-1, 1)
        );
    });

    // Stutter - rapid retriggering
    stutter = Mix.fill(6, {
        var baseRate = LFNoise0.kr(0.1).exprange(10, 80);
        var stutRate = baseRate * LFNoise0.kr(baseRate).range(1, 8);
        var freq = LFNoise0.kr(0.5).exprange(300, 6000);
        Pan2.ar(
            SinOsc.ar(freq, 0, Decay.ar(Impulse.ar(stutRate), 0.002) * 0.15),
            LFNoise1.kr(0.5).range(-1, 1)
        );
    });

    // Pure chaos - sample and hold madness
    chaos = SinOsc.ar(
        LFNoise0.ar(LFNoise0.kr(0.2).exprange(100, 2000)).exprange(200, 8000),
        0,
        0.15
    );
    chaos = Pan2.ar(chaos, LFNoise0.ar(50).range(-1, 1));

    mix = grains + bursts + stutter + chaos;
    mix = FreeVerb2.ar(mix[0], mix[1], 0.2, 0.5, 0.6);
    mix = Limiter.ar(mix * 0.8, 0.92);
    mix;
}.play;
)

// ============ GLACIAL DRONE ============
// Everything as slow as possible
// The forest over geological time
(
{
    var mix;
    var glacier, eons, breath, shift;

    // Glacier - evolving drone, changes over 30+ seconds
    glacier = Mix.fill(6, { |i|
        var freq = (30 + (i * 15)) * LFNoise1.kr(0.003).range(0.95, 1.05); // 0.003 Hz = 5+ min cycle
        var amp = LFNoise1.kr(0.005).range(0.1, 0.4);
        SinOsc.ar(freq * [1, 1.002], 0, amp); // slight detune for width
    });

    // Eons - noise filtered so slowly it becomes tone
    eons = LPF.ar(
        BrownNoise.ar(0.5),
        LFNoise1.kr(0.002).exprange(40, 400).lag(10) // 10 second lag on filter!
    );
    eons = Pan2.ar(eons, LFNoise1.kr(0.001).range(-0.5, 0.5));

    // Breath - the earth inhales over 30 seconds
    breath = SinOsc.ar(
        LFNoise1.kr(0.001).exprange(25, 60),
        0,
        SinOsc.kr(0.016).range(0, 0.5) // 0.016 Hz = 62 second cycle
    );
    breath = breath * [1, 1];

    // Shift - rare tectonic events
    shift = Ringz.ar(
        Dust.ar(0.01), // once every 100 seconds on average
        LFNoise0.kr(0.01).exprange(40, 200),
        LFNoise0.kr(0.05).range(5, 20) // 5-20 second decay
    ) * 0.6;
    shift = Pan2.ar(shift, LFNoise1.kr(0.01).range(-0.8, 0.8));

    mix = glacier + eons + breath + shift;
    mix = LPF.ar(mix, 500); // keep it low
    mix = FreeVerb2.ar(mix[0], mix[1], 0.8, 0.99, 0.05); // massive reverb
    mix = Limiter.ar(mix * 1.3, 0.94);
    mix;
}.play;
)

// ============ DONUT HOLE ============
// Sub-bass AND ultra-highs, NOTHING in between
// Two worlds that never touch
(
{
    var low, high, mix;
    var abyss, pressure, static, glass, ghost;

    // THE ABYSS (below 80Hz)
    abyss = Mix.fill(4, {
        var freq = LFNoise1.kr(0.008).exprange(12, 40);
        SinOsc.ar(freq, 0, LFNoise1.kr(0.02).range(0.2, 0.6));
    });
    pressure = LPF.ar(BrownNoise.ar(0.5), LFNoise1.kr(0.01).exprange(30, 80));
    low = abyss + pressure;
    low = LPF.ar(low, 80); // hard cut at 80Hz

    // THE ETHER (above 8kHz)
    static = HPF.ar(PinkNoise.ar(0.12), 10000);
    glass = Mix.fill(10, {
        var trig = Dust.ar(LFNoise0.kr(0.15).range(0.5, 8));
        var freq = LFNoise0.kr(0.3).exprange(9000, 18000);
        Ringz.ar(trig, freq, 0.003) * 0.08;
    });
    glass = Splay.ar(glass, 0.9);

    // Ghost tones - pure sines in the stratosphere
    ghost = Mix.fill(5, { |i|
        var freq = 10000 + (i * 1500) + LFNoise1.kr(0.05).range(-200, 200);
        SinOsc.ar(freq, 0, LFNoise1.kr(0.1).range(0, 0.02));
    });
    ghost = Pan2.ar(ghost, LFNoise1.kr(0.08).range(-0.6, 0.6));

    high = static + glass + ghost;
    high = HPF.ar(high, 8000); // hard cut at 8kHz

    // They never meet, but they breathe together
    low = low * SinOsc.kr(0.05).range(0.5, 1);
    high = high * SinOsc.kr(0.05, pi).range(0.5, 1); // opposite phase

    mix = low + high;
    mix = FreeVerb2.ar(mix[0], mix[1], 0.5, 0.85, 0.3);
    mix = Limiter.ar(mix * 1.4, 0.93);
    mix;
}.play;
)
