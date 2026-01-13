{
    var time = Line.kr(0, 1, 8);

    var clickRate = LinExp.kr(time, 0, 1, 2, 200);
    var clicks = Impulse.ar(clickRate) * 0.7;

    var clickPitch = TRand.ar(200, 8000, Impulse.ar(clickRate));
    var clickTone = SinOsc.ar(clickPitch) * Decay.ar(Impulse.ar(clickRate), 0.01);

    var panRate = LinExp.kr(time, 0, 1, 0.5, 20);
    var pan = SinOsc.kr(panRate);
    var clickStereo = Pan2.ar(clicks + clickTone, pan);

    var noise = WhiteNoise.ar(0.3);
    var localBuf = LocalBuf(2048, 1);
    var chain = FFT(localBuf, noise);
    var scrambled = PV_BinScramble(chain, LFNoise1.kr(3).range(0, 1), LFNoise0.kr(8).range(0, 0.5), Impulse.kr(5));
    var smeared = PV_MagSmear(scrambled, 10);

    var spectral = IFFT(smeared) * 0.5;
    var spectralStereo = Pan2.ar(spectral, LFNoise1.kr(7));

    var xfade = time.pow(2);
    var mix = (clickStereo * (1 - xfade)) + (spectralStereo * xfade);

    var ringMod = SinOsc.ar(LFNoise0.kr(12).range(100, 3000));
    mix = mix + (mix * ringMod * xfade * 0.3);

    mix * 0.6
}
