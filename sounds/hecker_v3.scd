{
    var gendy1, gendy2, dustL, dustR;
    var buf1, buf2, chain1, chain2, freeze1, freeze2;
    var spectral1, spectral2, left, right;
    var gateL, gateR, rupture, holdL, holdR;

    // Gendy foundation - same as v2
    gendy1 = Gendy1.ar(
        ampdist: LFNoise0.kr(0.3).range(0, 6),
        durdist: LFNoise0.kr(0.2).range(0, 6),
        adparam: LFNoise2.kr(0.5).range(0.1, 1.5),
        ddparam: LFNoise2.kr(0.4).range(0.1, 1.5),
        minfreq: LFNoise2.kr(0.1).exprange(20, 200),
        maxfreq: LFNoise2.kr(0.15).exprange(800, 12000),
        ampscale: 0.5,
        durscale: 0.5
    );

    gendy2 = Gendy2.ar(
        ampdist: LFNoise0.kr(0.25).range(0, 5),
        durdist: LFNoise0.kr(0.3).range(0, 5),
        adparam: LFNoise2.kr(0.6),
        ddparam: LFNoise2.kr(0.5),
        minfreq: LFNoise2.kr(0.08).exprange(50, 500),
        maxfreq: LFNoise2.kr(0.12).exprange(2000, 18000),
        a: LFNoise2.kr(0.2).range(0.1, 1.2),
        c: LFNoise2.kr(0.15).range(0.1, 0.9)
    ) * 0.6;

    // Aperiodic clicks - higher density for more transients
    dustL = Dust.ar(LFNoise2.kr(0.2).exprange(10, 300));
    dustR = Dust.ar(LFNoise2.kr(0.18).exprange(10, 300));

    // Spectral processing
    buf1 = LocalBuf(2048);
    buf2 = LocalBuf(2048);
    chain1 = FFT(buf1, gendy1);
    chain2 = FFT(buf2, gendy2);

    freeze1 = ToggleFF.kr(Dust.kr(LFNoise0.kr(0.1).range(0.5, 5)));
    freeze2 = ToggleFF.kr(Dust.kr(LFNoise0.kr(0.12).range(0.5, 5)));
    chain1 = PV_Freeze(chain1, freeze1);
    chain2 = PV_Freeze(chain2, freeze2);

    chain1 = PV_MagSmear(chain1, LFNoise0.kr(0.5).range(1, 30).asInteger);
    chain2 = PV_MagSmear(chain2, LFNoise0.kr(0.4).range(1, 30).asInteger);

    spectral1 = IFFT(chain1);
    spectral2 = IFFT(chain2);

    // === NEW: Temporal ruptures to restore roughness ===

    // Sample-and-hold on the signal itself - creates harsh stairstepping
    holdL = Latch.ar(spectral1 + gendy1, Dust.ar(LFNoise0.kr(0.3).exprange(100, 8000)));
    holdR = Latch.ar(spectral2 + gendy2, Dust.ar(LFNoise0.kr(0.25).exprange(100, 8000)));

    // Aperiodic gates that cut the signal suddenly
    gateL = Trig.ar(Dust.ar(LFNoise2.kr(0.15).range(2, 30)), LFNoise0.kr(3).range(0.01, 0.2));
    gateR = Trig.ar(Dust.ar(LFNoise2.kr(0.12).range(2, 30)), LFNoise0.kr(2.5).range(0.01, 0.2));

    // Random full-signal ruptures - brief silences
    rupture = Trig.kr(Dust.kr(LFNoise0.kr(0.1).range(0.3, 2)), LFNoise0.kr(0.5).range(0.05, 0.3));

    // Mix: held signal * gate, plus raw dust transients
    left = (holdL * gateL * 0.6) + (dustL * TRand.ar(-1, 1, dustL) * 0.4);
    right = (holdR * gateR * 0.6) + (dustR * TRand.ar(-1, 1, dustR) * 0.4);

    // Apply ruptures
    left = left * (1 - rupture);
    right = right * (1 - rupture);

    // Bit reduction for extra grit
    left = (left * 16).round / 16;
    right = (right * 16).round / 16;

    [left, right] * 0.4
}
