{
    var gendy1, gendy2, dustL, dustR, clicksL, clicksR;
    var buf1, buf2, chain1, chain2, freeze1, freeze2;
    var spectral1, spectral2, grainTrig, grainDur, grains;
    var panL, panR, left, right, ampMod;

    // Gendy - Xenakis stochastic synthesis
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
    ) * 0.4;

    // Aperiodic clicks
    dustL = Dust.ar(LFNoise2.kr(0.3).exprange(0.5, 80));
    dustR = Dust.ar(LFNoise2.kr(0.25).exprange(0.5, 80));
    clicksL = dustL * TRand.ar(-1, 1, dustL);
    clicksR = dustR * TRand.ar(-1, 1, dustR);

    // Spectral processing
    buf1 = LocalBuf(2048);
    buf2 = LocalBuf(2048);
    chain1 = FFT(buf1, gendy1);
    chain2 = FFT(buf2, gendy2);

    freeze1 = ToggleFF.kr(Dust.kr(LFNoise0.kr(0.1).range(0.2, 3)));
    freeze2 = ToggleFF.kr(Dust.kr(LFNoise0.kr(0.12).range(0.2, 3)));
    chain1 = PV_Freeze(chain1, freeze1);
    chain2 = PV_Freeze(chain2, freeze2);

    chain1 = PV_MagSmear(chain1, LFNoise0.kr(0.5).range(1, 50).asInteger);
    chain2 = PV_MagSmear(chain2, LFNoise0.kr(0.4).range(1, 50).asInteger);
    chain1 = PV_BinShift(chain1, LFNoise2.kr(0.3).range(0.5, 2), LFNoise2.kr(0.2).range(-100, 100));

    spectral1 = IFFT(chain1);
    spectral2 = IFFT(chain2);

    // Granular layer
    grainTrig = Dust.kr(LFNoise2.kr(0.2).range(5, 60));
    grainDur = TRand.kr(0.005, 0.15, grainTrig);
    grains = GrainIn.ar(2, grainTrig, grainDur, gendy1 + gendy2, TRand.kr(-1, 1, grainTrig)) * 0.3;

    // Aperiodic panning
    panL = LFNoise2.kr(LFNoise0.kr(0.1).range(0.1, 4));
    panR = LFNoise2.kr(LFNoise0.kr(0.12).range(0.1, 4));

    left = (spectral1 * 0.5) + (clicksL * 0.3) + (grains[0] * 0.4);
    right = (spectral2 * 0.5) + (clicksR * 0.3) + (grains[1] * 0.4);

    // Random amplitude ruptures
    ampMod = LFNoise0.kr(LFNoise2.kr(0.1).range(0.5, 8)).range(0.1, 1);

    [left, right] * ampMod * 0.5
}
